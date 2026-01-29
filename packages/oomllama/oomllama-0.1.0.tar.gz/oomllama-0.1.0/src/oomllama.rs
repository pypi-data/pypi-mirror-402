//! OomLlama.rs - The Sovereign LLM Runtime
//!
//! "OpenAI buys 40% of world's RAM. We build the solution that saves 90%."
//!
//! Core Goals:
//! - 7B Model in 1GB RAM (Q2 Quantization)
//! - TIBET-signed Inference
//! - Rust-native efficiency (Candle)
//! - **Lazy Layer Loading**: Only load active layer into RAM.

use candle_core::{Device, Tensor, DType, Shape};
use candle_nn::VarBuilder;
use candle_transformers::models::llama::{Config, Cache, LlamaEosToks};
// Note: We need a custom Llama implementation to support lazy loading effectively.
// For this PoC, we will wrap the standard model but use our custom loader.
// In a full implementation, we would rewrite the Llama model struct to hold "LazyTensor"s.

use hf_hub::{api::sync::Api, Repo, RepoType};
use tokenizers::Tokenizer;
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use uuid::Uuid;
use serde::Deserialize;
use crate::tibet::TibetFactory;
use crate::betti::{BettiManager, AllocationRequest, ResourceType, Humotica};
use crate::quant::OomLoader;

// Re-using the config struct
#[derive(Deserialize, Debug, Clone)]
struct LlamaConfig {
    pub hidden_size: usize,
    pub intermediate_size: usize,
    pub vocab_size: usize,
    pub num_hidden_layers: usize,
    pub num_attention_heads: usize,
    pub num_key_value_heads: Option<usize>,
    pub rms_norm_eps: f64,
    #[serde(default = "default_rope_theta")]
    pub rope_theta: f32,
    pub bos_token_id: Option<u32>,
    pub eos_token_id: Option<serde_json::Value>,
    pub max_position_embeddings: usize,
    #[serde(default)]
    pub tie_word_embeddings: bool,
}

fn default_rope_theta() -> f32 { 10000.0 }

impl From<LlamaConfig> for Config {
    fn from(c: LlamaConfig) -> Self {
        let eos_token_id = match c.eos_token_id {
            Some(serde_json::Value::Number(n)) => n.as_u64().map(|v| LlamaEosToks::Single(v as u32)),
            Some(serde_json::Value::Array(a)) => {
                let ids: Vec<u32> = a.iter().filter_map(|v| v.as_u64().map(|n| n as u32)).collect();
                Some(LlamaEosToks::Multiple(ids))
            }
            _ => None,
        };

        Config {
            hidden_size: c.hidden_size,
            intermediate_size: c.intermediate_size,
            vocab_size: c.vocab_size,
            num_hidden_layers: c.num_hidden_layers,
            num_attention_heads: c.num_attention_heads,
            num_key_value_heads: c.num_key_value_heads.unwrap_or(c.num_attention_heads),
            rms_norm_eps: c.rms_norm_eps,
            rope_theta: c.rope_theta,
            use_flash_attn: false,
            bos_token_id: c.bos_token_id,
            eos_token_id,
            max_position_embeddings: c.max_position_embeddings,
            rope_scaling: None,
            tie_word_embeddings: c.tie_word_embeddings,
        }
    }
}

// Helper to reverse map Config to LlamaConfig for shape inference (temporary hack)
impl From<Config> for LlamaConfig {
    fn from(c: Config) -> Self {
        LlamaConfig {
            hidden_size: c.hidden_size,
            intermediate_size: c.intermediate_size,
            vocab_size: c.vocab_size,
            num_hidden_layers: c.num_hidden_layers,
            num_attention_heads: c.num_attention_heads,
            num_key_value_heads: Some(c.num_key_value_heads),
            rms_norm_eps: c.rms_norm_eps,
            rope_theta: c.rope_theta,
            bos_token_id: c.bos_token_id,
            eos_token_id: None, // Simplified
            max_position_embeddings: c.max_position_embeddings,
            tie_word_embeddings: c.tie_word_embeddings,
        }
    }
}

// --- GHOST MODEL COMPONENTS ---

#[allow(dead_code)]
struct GhostLinear {
    weight: GhostLayer,
}

impl GhostLinear {
    fn new(name: &str, device: Device, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        Self { weight: GhostLayer::new(name.to_string(), device, loader, config) }
    }

    fn forward(&self, x: &Tensor) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        let w = self.weight.materialize()?;
        // Linear: x * W^T
        let res = x.matmul(&w.t()?)?;
        Ok(res)
    }
}

#[allow(dead_code)]
struct GhostRMSNorm {
    weight: GhostLayer,
    eps: f64,
}

impl GhostRMSNorm {
    fn new(name: &str, device: Device, loader: Arc<OomLoader>, config: LlamaConfig, eps: f64) -> Self {
        Self { 
            weight: GhostLayer::new(name.to_string(), device, loader, config),
            eps 
        }
    }

    fn forward(&self, x: &Tensor) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        let w = self.weight.materialize()?;
        // RMSNorm: x / sqrt(mean(x^2) + eps) * w
        let x_dtype = x.dtype();
        let x_f32 = x.to_dtype(DType::F32)?;
        let pow_2 = x_f32.sqr()?;
        let mean_pow_2 = pow_2.mean_keepdim(candle_core::D::Minus1)?;
        let norm_x = x_f32.broadcast_div(&(mean_pow_2 + self.eps)?.sqrt()?)?;
        let res = norm_x.broadcast_mul(&w)?;
        Ok(res.to_dtype(x_dtype)?)
    }
}

#[allow(dead_code)]
struct GhostMlp {
    gate_proj: GhostLinear,
    up_proj: GhostLinear,
    down_proj: GhostLinear,
}

impl GhostMlp {
    fn new(prefix: &str, device: Device, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        Self {
            gate_proj: GhostLinear::new(&format!("{}.gate_proj.weight", prefix), device.clone(), loader.clone(), config.clone()),
            up_proj: GhostLinear::new(&format!("{}.up_proj.weight", prefix), device.clone(), loader.clone(), config.clone()),
            down_proj: GhostLinear::new(&format!("{}.down_proj.weight", prefix), device, loader, config),
        }
    }

    fn forward(&self, x: &Tensor) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        let gate = self.gate_proj.forward(x)?;
        let up = self.up_proj.forward(x)?;
        // Simple approximation of SiLU: x * sigmoid(x)
        let activated_gate = (gate.clone() * candle_nn::ops::sigmoid(&gate)?)?;
        let intermediate = (activated_gate * up)?;
        self.down_proj.forward(&intermediate)
    }
}

#[allow(dead_code)]
struct GhostAttention {
    q_proj: GhostLinear,
    k_proj: GhostLinear,
    v_proj: GhostLinear,
    o_proj: GhostLinear,
    num_heads: usize,
    num_kv_heads: usize,
    head_dim: usize,
}

impl GhostAttention {
    fn new(prefix: &str, device: Device, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        Self {
            q_proj: GhostLinear::new(&format!("{}.q_proj.weight", prefix), device.clone(), loader.clone(), config.clone()),
            k_proj: GhostLinear::new(&format!("{}.k_proj.weight", prefix), device.clone(), loader.clone(), config.clone()),
            v_proj: GhostLinear::new(&format!("{}.v_proj.weight", prefix), device.clone(), loader.clone(), config.clone()),
            o_proj: GhostLinear::new(&format!("{}.o_proj.weight", prefix), device, loader, config.clone()),
            num_heads: config.num_attention_heads,
            num_kv_heads: config.num_key_value_heads.unwrap_or(config.num_attention_heads),
            head_dim: config.hidden_size / config.num_attention_heads,
        }
    }

    // Forward pass logic for attention will be added in Phase 3
}

#[allow(dead_code)]
struct GhostDecoderLayer {
    self_attn: GhostAttention,
    mlp: GhostMlp,
    input_layernorm: GhostRMSNorm,
    post_attention_layernorm: GhostRMSNorm,
}

impl GhostDecoderLayer {
    fn new(prefix: &str, device: Device, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        Self {
            self_attn: GhostAttention::new(&format!("{}.self_attn", prefix), device.clone(), loader.clone(), config.clone()),
            mlp: GhostMlp::new(&format!("{}.mlp", prefix), device.clone(), loader.clone(), config.clone()),
            input_layernorm: GhostRMSNorm::new(&format!("{}.input_layernorm.weight", prefix), device.clone(), loader.clone(), config.clone(), config.rms_norm_eps),
            post_attention_layernorm: GhostRMSNorm::new(&format!("{}.post_attention_layernorm.weight", prefix), device, loader, config.clone(), config.rms_norm_eps),
        }
    }
}

// --- GHOST MODEL ARCHITECTURE ---

/// Represents a tensor that resides on disk (Ghost) and can be materialized into VRAM.
#[allow(dead_code)]
struct GhostLayer {
    name: String,
    device: Device,
    loader: Arc<OomLoader>,
    config: LlamaConfig,
}

impl GhostLayer {
    #[allow(dead_code)]
    fn new(name: String, device: Device, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        Self { name, device, loader, config }
    }

    /// Materialize the ghost into a real Tensor in VRAM.
    /// This triggers the dequantization from disk -> RAM -> GPU.
    #[allow(dead_code)]
    fn materialize(&self) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        // 1. Dequantize from mmap to CPU buffer (f32)
        let data = self.loader.dequantize_tensor(&self.name)?;
        
        // 2. Infer shape from config (Hacky, but works for now)
        let shape = infer_shape(&self.name, &self.config);
        
        // 3. Upload to GPU/Device
        let tensor = Tensor::from_vec(data, shape, &self.device)?;
        
        Ok(tensor)
    }
}

/// Manages the lifecycle of GhostLayers.
/// Acts as a pseudo-VarBuilder that loads on demand.
/// NOTE: To fully integrate with Candle's Llama, we ideally need to rewrite Llama to use this directly.
/// For this Phase 2 PoC, we will keep the Model structure but intercept the weight loading?
/// Actually, Candle's `Llama` struct OWNS the tensors. It expects them loaded at init.
/// 
/// CRITICAL PIVOT: We cannot use standard `candle_transformers::models::llama::Llama` for Ghost Loading
/// without pre-loading everything. 
/// 
/// We need to implement a `GhostLlama` that executes layer-by-layer manually.
/// This is a big task. For now, we will simulate it by implementing a `GhostLoader` struct
/// that we can query. 
///
/// But wait! If we use `VarBuilder` with a custom backend?
/// Candle's VarBuilder reads everything into Tensors eagerly when the model is instantiated.
///
/// SOLUTION: We will implement our OWN minimal Llama inference loop here that uses GhostLayers.
/// Or, we use the `OomLlama` to hold the `GhostLayers` map, and we build a custom runner.
///
/// Let's build the `GhostLlama` struct.

#[allow(dead_code)]
struct GhostLlamaModel {
    embed_tokens: GhostLayer,
    layers: Vec<GhostDecoderLayer>,
    norm: GhostRMSNorm,
    lm_head: GhostLinear,
    // Dual GPU support: store both devices for tensor transfers
    devices: Vec<Device>,
}

impl GhostLlamaModel {
    fn new(primary_device: Device, secondary_device: Option<Device>, loader: Arc<OomLoader>, config: LlamaConfig) -> Self {
        let mut layers = Vec::new();

        // Dual GPU: alternate layers between devices
        let has_dual_gpu = secondary_device.is_some();
        let gpu1 = secondary_device.unwrap_or_else(|| primary_device.clone());

        for i in 0..config.num_hidden_layers {
            // Even layers -> primary GPU, Odd layers -> secondary GPU
            let layer_device = if has_dual_gpu && i % 2 == 1 {
                gpu1.clone()
            } else {
                primary_device.clone()
            };
            layers.push(GhostDecoderLayer::new(&format!("model.layers.{}", i), layer_device, loader.clone(), config.clone()));
        }

        if has_dual_gpu {
            println!("🔀 DUAL GPU MODE: Even layers → GPU 0, Odd layers → GPU 1");
        }

        Self {
            embed_tokens: GhostLayer::new("model.embed_tokens.weight".to_string(), primary_device.clone(), loader.clone(), config.clone()),
            layers,
            norm: GhostRMSNorm::new("model.norm.weight", primary_device.clone(), loader.clone(), config.clone(), config.rms_norm_eps),
            lm_head: GhostLinear::new("lm_head.weight", primary_device.clone(), loader, config),
            devices: vec![primary_device, gpu1],
        }
    }

    fn forward(&self, tokens: &Tensor) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        // Check if we have dual GPU
        let dual_gpu = self.devices.len() > 1 && self.devices[0].is_cuda() && self.devices[1].is_cuda();

        // 1. Embeddings (Materialize -> Gather -> Evict) - Always on primary GPU
        let mut x = {
            let embed_w = self.embed_tokens.materialize()?;
            embed_w.embedding(&tokens.flatten_all()?)?
        };

        // 2. Decoder Layers (The Ghost Loop)
        for (i, layer) in self.layers.iter().enumerate() {
            if i % 10 == 0 {
                println!("👻 Ghost processing layer {}/{}...", i, self.layers.len());
            }

            // DUAL GPU: Transfer tensor to correct device before processing layer
            if dual_gpu {
                let target_device = if i % 2 == 1 { &self.devices[1] } else { &self.devices[0] };
                if x.device().location() != target_device.location() {
                    x = x.to_device(target_device)?;
                }
            }

            let residual = x.clone();
            x = layer.input_layernorm.forward(&x)?;

            // --- GHOST ATTENTION ---
            // Each projection is materialized and evicted individually
            let q = layer.self_attn.q_proj.forward(&x)?;
            let k = layer.self_attn.k_proj.forward(&x)?;
            let v = layer.self_attn.v_proj.forward(&x)?;

            // (Scaled Dot Product Attention logic omitted for PoC, using 'q' as placeholder)
            let attn_output = q;

            x = layer.self_attn.o_proj.forward(&attn_output)?;
            x = (x + residual)?;

            // --- GHOST MLP ---
            let residual = x.clone();
            x = layer.post_attention_layernorm.forward(&x)?;
            x = layer.mlp.forward(&x)?;
            x = (x + residual)?;
        }

        // 3. Final Norm - Transfer back to primary GPU
        if dual_gpu {
            x = x.to_device(&self.devices[0])?;
        }
        x = self.norm.forward(&x)?;

        // 4. LM Head (Final Ghost)
        self.lm_head.forward(&x)
    }
}

pub struct GhostLlama {
    // Model state
    #[allow(dead_code)]
    config: Config,
    #[allow(dead_code)]
    tokenizer: Tokenizer,
    #[allow(dead_code)]
    device: Device,
    
    // Ghost Model
    model: GhostLlamaModel,
    
    // Shared weight loader
    loader: Arc<OomLoader>,
    
    // Domain-AI Context (Temporary knowledge)
    active_context: Option<String>,
    
    // TIBET & Betti
    tibet: TibetFactory,
    betti: Arc<BettiManager>,
    allocation_id: Option<Uuid>,
    name: String,
}

impl GhostLlama {
    /// Create a new GhostLlama instance.
    /// - `gpu_index`: Primary GPU (None = CPU)
    /// - `secondary_gpu`: Optional second GPU for dual-GPU layer striping
    pub fn new(name: &str, gpu_index: Option<usize>, betti: Arc<BettiManager>, model_path: Option<&str>, tokenizer_path: Option<&str>) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        // NEW: Also try to initialize secondary GPU for dual-GPU mode
        let secondary_gpu: Option<usize> = if gpu_index.is_some() {
            // Try GPU 1 if primary is GPU 0, or GPU 0 if primary is something else
            let secondary_idx = if gpu_index == Some(0) { 1 } else { 0 };
            if Device::new_cuda(secondary_idx).is_ok() {
                println!("🎮 Secondary GPU {} detected - enabling dual GPU mode!", secondary_idx);
                Some(secondary_idx)
            } else {
                None
            }
        } else {
            None
        };

        let resource_type = if gpu_index.is_some() { ResourceType::Gpu } else { ResourceType::Cpu };

        // Request allocation
        let req = AllocationRequest {
            idd_name: name.to_string(),
            resource_type,
            amount: if secondary_gpu.is_some() { 3.0 } else { 1.5 }, // Double for dual GPU
            duration_secs: None,
            purpose: "Ghost Model Inference".to_string(),
            priority: 90,
            humotica: Some(Humotica {
                sense: "Inference".to_string(),
                context: if secondary_gpu.is_some() { "Ghost Model (70B) - DUAL GPU" } else { "Ghost Model (70B)" }.to_string(),
                intent: "Sovereign AI".to_string(),
                explanation: if secondary_gpu.is_some() {
                    "Running 70B model with dual GPU layer striping".to_string()
                } else {
                    "Running 70B model with 1GB VRAM paging".to_string()
                },
            }),
        };
        let allocation = betti.request(req).ok().map(|a| a.id);

        let device = match gpu_index {
            Some(idx) => Device::new_cuda(idx).unwrap_or(Device::Cpu),
            None => Device::Cpu,
        };

        let secondary_device = secondary_gpu.and_then(|idx| Device::new_cuda(idx).ok());

        // Load Tokenizer
        let tokenizer = if let Some(path) = tokenizer_path {
            Tokenizer::from_file(path).map_err(|e| e.to_string())?
        } else {
            let api = Api::new()?;
            let repo = api.repo(Repo::new("TinyLlama/TinyLlama-1.1B-Chat-v1.0".to_string(), RepoType::Model));
            let filename = repo.get("tokenizer.json")?;
            Tokenizer::from_file(filename).map_err(|e| e.to_string())?
        };

        let config: Config = if let Some(path) = model_path {
             let model_dir = std::path::Path::new(path).parent().unwrap_or(std::path::Path::new("."));
             let config_path = model_dir.join("config.json");
             
             // FORCE 70B/72B if markers found in filename
             if path.contains("llamaohm") || path.contains("llama-70b") || path.contains("llama3") {
                 // Llama 3.3 70B Instruct config
                 println!("🦙 LLAMA 3.3 70B DETECTED: Using Llama config (Hidden: 8192, Vocab: 128256).");
                 Config {
                    hidden_size: 8192,
                    intermediate_size: 28672,
                    vocab_size: 128256, // Llama 3.3 vocab
                    num_hidden_layers: 80,
                    num_attention_heads: 64,
                    num_key_value_heads: 8,
                    rms_norm_eps: 1e-5,
                    rope_theta: 500000.0,
                    use_flash_attn: false,
                    bos_token_id: Some(128000),
                    eos_token_id: Some(LlamaEosToks::Single(128001)),
                    max_position_embeddings: 131072,
                    rope_scaling: None,
                    tie_word_embeddings: false,
                 }
             } else if path.contains("32b") || path.contains("humotica-32") {
                 // Qwen 2.5 32B config (OomLlama's native brain!)
                 println!("🦙 QWEN 32B DETECTED: OomLlama's brain! (Hidden: 5120, 64 layers, Vocab: 152064)");
                 Config {
                    hidden_size: 5120,
                    intermediate_size: 27648,
                    vocab_size: 152064, // Qwen 2.5 vocab
                    num_hidden_layers: 64,
                    num_attention_heads: 40,
                    num_key_value_heads: 8,
                    rms_norm_eps: 1e-6,
                    rope_theta: 1000000.0,
                    use_flash_attn: false,
                    bos_token_id: Some(151643),
                    eos_token_id: Some(LlamaEosToks::Single(151645)),
                    max_position_embeddings: 131072,
                    rope_scaling: None,
                    tie_word_embeddings: false,
                 }
             } else if path.contains("70b") || path.contains("72b") || path.contains("humotica-72") || path.contains("qwen") {
                 // Qwen 2.5 72B config
                 println!("🐘 QWEN 72B DETECTED: Using Qwen config (Hidden: 8192, Vocab: 152064).");
                 Config {
                    hidden_size: 8192,
                    intermediate_size: 28672,
                    vocab_size: 152064, // Qwen 2.5 default vocab
                    num_hidden_layers: 80,
                    num_attention_heads: 64,
                    num_key_value_heads: 8,
                    rms_norm_eps: 1e-5,
                    rope_theta: 500000.0,
                    use_flash_attn: false,
                    bos_token_id: Some(151643),
                    eos_token_id: Some(LlamaEosToks::Single(151645)),
                    max_position_embeddings: 8192,
                    rope_scaling: None,
                    tie_word_embeddings: false,
                 }
             } else if config_path.exists() {
                 println!("📜 Found local config: {:?}", config_path);
                 let l_config: LlamaConfig = serde_json::from_str(&std::fs::read_to_string(config_path)?)?;
                 Config::from(l_config)
             } else {
                 println!("🐑 Falling back to TinyLlama default config.");
                 let api = Api::new()?;
                 let repo = api.repo(Repo::new("TinyLlama/TinyLlama-1.1B-Chat-v1.0".to_string(), RepoType::Model));
                 let filename = repo.get("config.json")?;
                 let l_config: LlamaConfig = serde_json::from_str(&std::fs::read_to_string(filename)?)?;
                 Config::from(l_config)
             }
        } else {
             let api = Api::new()?;
             let repo = api.repo(Repo::new("TinyLlama/TinyLlama-1.1B-Chat-v1.0".to_string(), RepoType::Model));
             let filename = repo.get("config.json")?;
             let l_config: LlamaConfig = serde_json::from_str(&std::fs::read_to_string(filename)?)?;
             Config::from(l_config)
        };

        let loader = if let Some(path) = model_path {
            if path.ends_with(".oom") { Arc::new(OomLoader::load(path)?) }
            else { return Err("Ghost Model requires .oom file".into()); }
        } else {
            let path = "data/kmbit/models/tinyllama_q4.oom";
            if std::path::Path::new(path).exists() { Arc::new(OomLoader::load(path)?) }
            else { return Err("No model found. Please provide --model <path.oom>".into()); }
        };

        let model = GhostLlamaModel::new(device.clone(), secondary_device, loader.clone(), LlamaConfig::from(config.clone()));

        Ok(Self {
            config,
            tokenizer,
            device,
            model,
            loader,
            active_context: None,
            tibet: TibetFactory::new(name),
            betti,
            allocation_id: allocation,
            name: name.to_string(),
        })
    }

    /// Inject temporary domain context (Vertical Virtual Fun)
    pub fn push_context(&mut self, context: &str) {
        println!("💉 Brain: Absorbing new context ({} bytes)...", context.len());
        self.active_context = Some(context.to_string());
    }

    pub fn infer(&mut self, prompt: &str, max_tokens: usize) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let _token = self.tibet.action("GhostInference", &self.name, serde_json::json!({ "prompt": prompt }));

        // Incorporate context into prompt
        let context_prefix = if let Some(ctx) = &self.active_context {
            format!("### EXTRA CONTEXT:\n{}\n\n", ctx)
        } else {
            "".to_string()
        };

        let full_prompt = format!("{}USER: {}\nASSISTANT:", context_prefix, prompt);
        let tokens = self.tokenizer.encode(full_prompt, true).map_err(|e| e.to_string())?.get_ids().to_vec();
        let input = Tensor::new(tokens, &self.device)?.unsqueeze(0)?;

        println!("🤖 Ghost Inference starting (70B ready)...");

        // Autoregressive generation loop
        let mut generated_tokens: Vec<u32> = Vec::new();
        let mut current_input = input;

        for i in 0..max_tokens {
            // Forward pass
            let logits = self.model.forward(&current_input)?;

            // Get logits for the last token position
            let seq_len = logits.dim(1)?;
            let last_logits = logits.narrow(1, seq_len - 1, 1)?.squeeze(1)?; // [1, vocab_size]

            // Greedy decoding: argmax
            let next_token = last_logits.argmax(candle_core::D::Minus1)?.to_scalar::<u32>()?;

            // Check for EOS token (common EOS IDs: 2, 151643 for Qwen, 128001 for Llama)
            if next_token == 2 || next_token == 151643 || next_token == 128001 {
                println!("🛑 EOS token reached at step {}", i);
                break;
            }

            generated_tokens.push(next_token);

            // Prepare next input (just the new token for KV-cache, or full sequence without)
            // For simplicity without KV-cache: append and continue
            let new_token = Tensor::new(&[next_token], &self.device)?.unsqueeze(0)?;
            current_input = Tensor::cat(&[&current_input, &new_token], 1)?;

            if i % 5 == 0 {
                println!("🔤 Generated {} tokens...", i + 1);
            }
        }

        println!("✅ Generation complete ({} tokens).", generated_tokens.len());

        // Decode tokens to text
        let output = self.tokenizer.decode(&generated_tokens, true).map_err(|e| e.to_string())?;

        Ok(output)
    }

    fn load_tensor(&self, name: &str) -> Result<Tensor, Box<dyn std::error::Error + Send + Sync>> {
        let l_config: LlamaConfig = self.config.clone().into(); // Hacky back-conversion
        let ghost = GhostLayer::new(name.to_string(), self.device.clone(), self.loader.clone(), l_config);
        ghost.materialize()
    }
}

// Rename OomLlama to GhostLlama in the rest of the file or use a type alias
pub type OomLlama = GhostLlama;

fn infer_shape(name: &str, config: &LlamaConfig) -> Shape {
    if name.contains("embed_tokens") {
        return Shape::from((config.vocab_size, config.hidden_size));
    }
    if name.contains("lm_head") {
        return Shape::from((config.vocab_size, config.hidden_size));
    }
    if name.contains("input_layernorm") || name.contains("post_attention_layernorm") || name == "model.norm.weight" {
        return Shape::from((config.hidden_size,));
    }
    if name.contains("q_proj") || name.contains("k_proj") || name.contains("v_proj") || name.contains("o_proj") {
        if name.contains("k_proj") || name.contains("v_proj") {
            let kv_heads = config.num_key_value_heads.unwrap_or(config.num_attention_heads);
            let head_dim = config.hidden_size / config.num_attention_heads;
            return Shape::from((kv_heads * head_dim, config.hidden_size));
        }
        return Shape::from((config.hidden_size, config.hidden_size));
    }
    if name.contains("gate_proj") || name.contains("up_proj") {
        return Shape::from((config.intermediate_size, config.hidden_size));
    }
    if name.contains("down_proj") {
        return Shape::from((config.hidden_size, config.intermediate_size));
    }
    Shape::from((0,)) // Fallback
}

impl Drop for GhostLlama {
    fn drop(&mut self) {
        if let Some(id) = self.allocation_id {
            let _ = self.betti.release(id);
        }
    }
}
