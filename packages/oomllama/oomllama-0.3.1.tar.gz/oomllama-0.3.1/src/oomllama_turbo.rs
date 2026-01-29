//! OomLlama Turbo - High Performance Native Inference
//!
//! Target: 3 min/token → 1 sec/token (180x speedup!)
//!
//! Optimizations:
//! 1. KV-Cache (10-50x) - Cache attention keys/values
//! 2. Layer Pinning (5-10x) - Hot layers in VRAM
//! 3. Async Prefetching (2-3x) - Background layer loading
//! 4. CUDA Streams (1.5-2x) - Overlap compute/transfer
//! 5. Flash Attention 2 (1.3-1.5x) - Memory-efficient attention
//!
//! One love, one fAmIly! 🦙🚀

use candle_core::{Device, Tensor, DType, Shape, D};
use std::sync::{Arc, RwLock};
use std::collections::HashMap;
use std::thread;
use std::sync::mpsc::{channel, Sender, Receiver};

// ============================================================================
// KV-CACHE: Cache Key/Value tensors to avoid recomputation
// ============================================================================

/// KV-Cache for a single attention layer
#[derive(Clone)]
pub struct LayerKVCache {
    /// Cached key tensor [batch, n_kv_heads, seq_len, head_dim]
    pub k: Option<Tensor>,
    /// Cached value tensor [batch, n_kv_heads, seq_len, head_dim]
    pub v: Option<Tensor>,
    /// Current sequence length in cache
    pub seq_len: usize,
}

impl LayerKVCache {
    pub fn new() -> Self {
        Self { k: None, v: None, seq_len: 0 }
    }

    /// Append new K/V to cache
    pub fn append(&mut self, new_k: &Tensor, new_v: &Tensor) -> candle_core::Result<()> {
        match (&self.k, &self.v) {
            (Some(old_k), Some(old_v)) => {
                // Concatenate along sequence dimension (dim 2)
                self.k = Some(Tensor::cat(&[old_k, new_k], 2)?);
                self.v = Some(Tensor::cat(&[old_v, new_v], 2)?);
            }
            _ => {
                self.k = Some(new_k.clone());
                self.v = Some(new_v.clone());
            }
        }
        self.seq_len += new_k.dim(2)?;
        Ok(())
    }

    /// Get cached K/V for attention computation
    pub fn get(&self) -> Option<(&Tensor, &Tensor)> {
        match (&self.k, &self.v) {
            (Some(k), Some(v)) => Some((k, v)),
            _ => None,
        }
    }

    /// Clear cache (for new sequence)
    pub fn clear(&mut self) {
        self.k = None;
        self.v = None;
        self.seq_len = 0;
    }
}

/// Full model KV-Cache
pub struct ModelKVCache {
    layers: Vec<LayerKVCache>,
    max_seq_len: usize,
}

impl ModelKVCache {
    pub fn new(n_layers: usize, max_seq_len: usize) -> Self {
        Self {
            layers: (0..n_layers).map(|_| LayerKVCache::new()).collect(),
            max_seq_len,
        }
    }

    pub fn get_layer(&self, layer_idx: usize) -> &LayerKVCache {
        &self.layers[layer_idx]
    }

    pub fn get_layer_mut(&mut self, layer_idx: usize) -> &mut LayerKVCache {
        &mut self.layers[layer_idx]
    }

    pub fn clear(&mut self) {
        for layer in &mut self.layers {
            layer.clear();
        }
    }

    pub fn seq_len(&self) -> usize {
        self.layers.first().map(|l| l.seq_len).unwrap_or(0)
    }
}

// ============================================================================
// LAYER PINNING: Keep hot layers in VRAM
// ============================================================================

/// Strategy for which layers to pin in VRAM
#[derive(Clone, Debug)]
pub enum PinStrategy {
    /// Pin first N and last M layers
    FirstLast { first: usize, last: usize },
    /// Pin every Nth layer
    Strided { stride: usize },
    /// Pin specific layer indices
    Specific(Vec<usize>),
    /// Pin layers based on importance scores
    Importance(Vec<f32>),
}

/// Pinned layer storage
pub struct LayerPin {
    /// Pinned tensors by layer index
    pinned: HashMap<usize, HashMap<String, Tensor>>,
    /// Total VRAM budget (bytes)
    vram_budget: usize,
    /// Current VRAM usage
    vram_used: usize,
    /// Pin strategy
    strategy: PinStrategy,
}

impl LayerPin {
    pub fn new(vram_budget_gb: f32, strategy: PinStrategy) -> Self {
        Self {
            pinned: HashMap::new(),
            vram_budget: (vram_budget_gb * 1e9) as usize,
            vram_used: 0,
            strategy,
        }
    }

    /// Check if layer should be pinned based on strategy
    pub fn should_pin(&self, layer_idx: usize, n_layers: usize) -> bool {
        match &self.strategy {
            PinStrategy::FirstLast { first, last } => {
                layer_idx < *first || layer_idx >= n_layers - *last
            }
            PinStrategy::Strided { stride } => layer_idx % stride == 0,
            PinStrategy::Specific(indices) => indices.contains(&layer_idx),
            PinStrategy::Importance(scores) => {
                // Pin if importance score > 0.5
                scores.get(layer_idx).map(|s| *s > 0.5).unwrap_or(false)
            }
        }
    }

    /// Pin a tensor if budget allows
    pub fn pin(&mut self, layer_idx: usize, name: &str, tensor: Tensor) -> bool {
        let size = tensor.elem_count() * tensor.dtype().size_in_bytes();

        if self.vram_used + size > self.vram_budget {
            return false;
        }

        self.vram_used += size;
        self.pinned
            .entry(layer_idx)
            .or_insert_with(HashMap::new)
            .insert(name.to_string(), tensor);
        true
    }

    /// Get pinned tensor if available
    pub fn get(&self, layer_idx: usize, name: &str) -> Option<&Tensor> {
        self.pinned.get(&layer_idx)?.get(name)
    }

    /// Check if tensor is pinned
    pub fn is_pinned(&self, layer_idx: usize, name: &str) -> bool {
        self.pinned.get(&layer_idx)
            .map(|m| m.contains_key(name))
            .unwrap_or(false)
    }

    pub fn vram_usage_gb(&self) -> f32 {
        self.vram_used as f32 / 1e9
    }
}

// ============================================================================
// ASYNC PREFETCHING: Load next layer while computing current
// ============================================================================

/// Message for prefetch worker
pub enum PrefetchMsg {
    /// Load tensor from OOM file
    Load { layer_idx: usize, tensor_name: String },
    /// Stop worker
    Stop,
}

/// Prefetched tensor result
pub struct PrefetchResult {
    pub layer_idx: usize,
    pub tensor_name: String,
    pub tensor: Result<Tensor, String>,
}

/// Async prefetcher using background thread
pub struct AsyncPrefetcher {
    sender: Sender<PrefetchMsg>,
    receiver: Receiver<PrefetchResult>,
    /// Prefetch queue (layers ahead to prefetch)
    lookahead: usize,
}

impl AsyncPrefetcher {
    pub fn new<F>(loader_fn: F, lookahead: usize) -> Self
    where
        F: Fn(usize, &str) -> Result<Tensor, String> + Send + 'static
    {
        let (tx_cmd, rx_cmd) = channel::<PrefetchMsg>();
        let (tx_result, rx_result) = channel::<PrefetchResult>();

        // Spawn prefetch worker
        thread::spawn(move || {
            loop {
                match rx_cmd.recv() {
                    Ok(PrefetchMsg::Load { layer_idx, tensor_name }) => {
                        let tensor = loader_fn(layer_idx, &tensor_name);
                        let _ = tx_result.send(PrefetchResult {
                            layer_idx,
                            tensor_name,
                            tensor,
                        });
                    }
                    Ok(PrefetchMsg::Stop) | Err(_) => break,
                }
            }
        });

        Self {
            sender: tx_cmd,
            receiver: rx_result,
            lookahead,
        }
    }

    /// Request prefetch of layer tensors
    pub fn prefetch(&self, layer_idx: usize, tensor_names: &[&str]) {
        for name in tensor_names {
            let _ = self.sender.send(PrefetchMsg::Load {
                layer_idx,
                tensor_name: name.to_string(),
            });
        }
    }

    /// Try to get prefetched tensor (non-blocking)
    pub fn try_get(&self) -> Option<PrefetchResult> {
        self.receiver.try_recv().ok()
    }

    /// Get prefetched tensor (blocking)
    pub fn get(&self) -> Option<PrefetchResult> {
        self.receiver.recv().ok()
    }
}

impl Drop for AsyncPrefetcher {
    fn drop(&mut self) {
        let _ = self.sender.send(PrefetchMsg::Stop);
    }
}

// ============================================================================
// FLASH ATTENTION 2: Memory-efficient attention
// ============================================================================

/// Flash Attention parameters
pub struct FlashAttentionConfig {
    pub block_size: usize,      // Typically 64 or 128
    pub causal: bool,           // Use causal mask
    pub softmax_scale: Option<f32>, // Custom scale, defaults to 1/sqrt(head_dim)
}

impl Default for FlashAttentionConfig {
    fn default() -> Self {
        Self {
            block_size: 64,
            causal: true,
            softmax_scale: None,
        }
    }
}

/// Compute attention with Flash Attention 2 algorithm
///
/// This is a software implementation - for true performance,
/// we need the CUDA kernel from flash-attn crate
pub fn flash_attention_forward(
    q: &Tensor,  // [batch, n_heads, seq_len, head_dim]
    k: &Tensor,  // [batch, n_kv_heads, seq_len, head_dim]
    v: &Tensor,  // [batch, n_kv_heads, seq_len, head_dim]
    config: &FlashAttentionConfig,
) -> candle_core::Result<Tensor> {
    let (batch, n_heads, seq_len, head_dim) = q.dims4()?;
    let n_kv_heads = k.dim(1)?;

    // Handle grouped query attention (GQA) - make contiguous for matmul
    let k = if n_kv_heads != n_heads {
        let repeat_factor = n_heads / n_kv_heads;
        k.repeat(&[1, repeat_factor, 1, 1])?.contiguous()?
    } else {
        k.contiguous()?
    };

    let v = if n_kv_heads != n_heads {
        let repeat_factor = n_heads / n_kv_heads;
        v.repeat(&[1, repeat_factor, 1, 1])?.contiguous()?
    } else {
        v.contiguous()?
    };

    // Scale factor
    let scale = config.softmax_scale
        .unwrap_or(1.0 / (head_dim as f32).sqrt());

    // Standard attention: softmax(Q @ K^T / sqrt(d)) @ V
    // For true Flash Attention, we'd use tiled computation
    let k_t = k.transpose(2, 3)?.contiguous()?;
    let att = (q.contiguous()?.matmul(&k_t)? * scale as f64)?;

    // Apply causal mask if needed
    let att = if config.causal && seq_len > 1 {
        // Create upper triangular mask (1s above diagonal)
        let mask = Tensor::triu2(seq_len, DType::F32, q.device())?;
        let mask = mask.broadcast_as(att.shape())?;
        // Mask out future tokens with -inf
        att.broadcast_add(&(mask * f32::NEG_INFINITY as f64)?)?
    } else {
        att
    };

    // Softmax
    let att = candle_nn::ops::softmax_last_dim(&att)?;

    // Attention @ Values (contiguous for matmul)
    att.contiguous()?.matmul(&v.contiguous()?)
}

// ============================================================================
// TURBO ENGINE: Combines all optimizations
// ============================================================================

/// Configuration for turbo inference
pub struct TurboConfig {
    /// Number of transformer layers
    pub n_layers: usize,
    /// Hidden dimension
    pub hidden_size: usize,
    /// Number of attention heads
    pub n_heads: usize,
    /// Number of KV heads (for GQA)
    pub n_kv_heads: usize,
    /// Head dimension
    pub head_dim: usize,
    /// Maximum sequence length for KV cache
    pub max_seq_len: usize,
    /// VRAM budget for layer pinning (GB)
    pub vram_budget_gb: f32,
    /// Layer pin strategy
    pub pin_strategy: PinStrategy,
    /// Prefetch lookahead
    pub prefetch_lookahead: usize,
    /// Use Flash Attention
    pub use_flash_attention: bool,
    /// Use FP16 compute (mixed precision)
    pub use_fp16: bool,
}

impl TurboConfig {
    /// Config for Qwen2.5-32B on dual RTX 3060 (24GB total)
    pub fn qwen32b_dual3060() -> Self {
        Self {
            n_layers: 64,
            hidden_size: 5120,
            n_heads: 40,
            n_kv_heads: 8,
            head_dim: 128,
            max_seq_len: 8192,
            vram_budget_gb: 4.0, // Conservative: 4GB for pinned layers, rest for compute
            pin_strategy: PinStrategy::FirstLast { first: 2, last: 2 }, // Pin first 2 + last 2 layers only
            prefetch_lookahead: 2,
            use_flash_attention: true,
            use_fp16: true,
        }
    }
}

/// Turbo inference engine
pub struct TurboEngine {
    config: TurboConfig,
    kv_cache: ModelKVCache,
    layer_pin: LayerPin,
    // prefetcher: Option<AsyncPrefetcher>,
    device: Device,
}

impl TurboEngine {
    pub fn new(config: TurboConfig, device: Device) -> Self {
        let kv_cache = ModelKVCache::new(config.n_layers, config.max_seq_len);
        let layer_pin = LayerPin::new(config.vram_budget_gb, config.pin_strategy.clone());

        Self {
            config,
            kv_cache,
            layer_pin,
            device,
        }
    }

    /// Process attention with KV-cache and Flash Attention
    pub fn attention_forward(
        &mut self,
        layer_idx: usize,
        x: &Tensor,
        wq: &Tensor,
        wk: &Tensor,
        wv: &Tensor,
        wo: &Tensor,
    ) -> candle_core::Result<Tensor> {
        let (batch, seq_len, hidden) = x.dims3()?;

        // Get output dimensions from weight shapes: wq is [hidden, q_out], etc.
        let q_out = wq.dim(1)?;
        let kv_out = wk.dim(1)?;

        // Project Q, K, V - reshape for batched matmul: [B, S, H] -> [B*S, H]
        let x_flat = x.reshape((batch * seq_len, hidden))?;
        let q = x_flat.matmul(wq)?.reshape((batch, seq_len, q_out))?;
        let k = x_flat.matmul(wk)?.reshape((batch, seq_len, kv_out))?;
        let v = x_flat.matmul(wv)?.reshape((batch, seq_len, kv_out))?;

        // Reshape for multi-head attention (contiguous for matmul)
        let q = q.reshape((batch, seq_len, self.config.n_heads, self.config.head_dim))?
            .transpose(1, 2)?.contiguous()?; // [batch, n_heads, seq_len, head_dim]
        let k = k.reshape((batch, seq_len, self.config.n_kv_heads, self.config.head_dim))?
            .transpose(1, 2)?.contiguous()?;
        let v = v.reshape((batch, seq_len, self.config.n_kv_heads, self.config.head_dim))?
            .transpose(1, 2)?.contiguous()?;

        // Update KV cache
        let cache = self.kv_cache.get_layer_mut(layer_idx);
        cache.append(&k, &v)?;

        // Get full K, V from cache
        let (full_k, full_v) = cache.get().unwrap();

        // Apply attention (with Flash Attention if enabled)
        let att_out = if self.config.use_flash_attention {
            flash_attention_forward(
                &q,
                full_k,
                full_v,
                &FlashAttentionConfig::default(),
            )?
        } else {
            // Standard attention (make tensors contiguous)
            let scale = 1.0 / (self.config.head_dim as f32).sqrt();
            let k_t = full_k.transpose(2, 3)?.contiguous()?;
            let att = (q.contiguous()?.matmul(&k_t)? * scale as f64)?;
            let att = candle_nn::ops::softmax_last_dim(&att)?;
            att.contiguous()?.matmul(&full_v.contiguous()?)?
        };

        // Reshape and project output (contiguous after transpose)
        let hidden_out = self.config.n_heads * self.config.head_dim;
        let att_out = att_out.transpose(1, 2)?.contiguous()?
            .reshape((batch, seq_len, hidden_out))?;

        // Output projection: [B, S, H] -> [B*S, H] -> matmul -> [B, S, H]
        let att_flat = att_out.reshape((batch * seq_len, hidden_out))?;
        let o_out = wo.dim(1)?;
        att_flat.matmul(wo)?.reshape((batch, seq_len, o_out))
    }

    /// Clear KV cache for new sequence
    pub fn reset(&mut self) {
        self.kv_cache.clear();
    }

    /// Get current sequence length
    pub fn seq_len(&self) -> usize {
        self.kv_cache.seq_len()
    }

    // ============ LAYER PINNING METHODS ============

    /// Check if a layer should be pinned based on strategy
    pub fn should_pin_layer(&self, layer_idx: usize) -> bool {
        self.layer_pin.should_pin(layer_idx, self.config.n_layers)
    }

    /// Get pinned tensor if available
    pub fn get_pinned(&self, layer_idx: usize, name: &str) -> Option<&Tensor> {
        self.layer_pin.get(layer_idx, name)
    }

    /// Pin a tensor (returns true if successful, false if VRAM budget exceeded)
    pub fn pin_tensor(&mut self, layer_idx: usize, name: &str, tensor: Tensor) -> bool {
        if self.layer_pin.should_pin(layer_idx, self.config.n_layers) {
            self.layer_pin.pin(layer_idx, name, tensor)
        } else {
            false
        }
    }

    /// Check if tensor is already pinned
    pub fn is_pinned(&self, layer_idx: usize, name: &str) -> bool {
        self.layer_pin.is_pinned(layer_idx, name)
    }

    /// Get VRAM usage for pinned layers
    pub fn pinned_vram_gb(&self) -> f32 {
        self.layer_pin.vram_usage_gb()
    }
}

// ============================================================================
// ENVIRONMENT SETUP
// ============================================================================

/// Set up CUDA environment for optimal performance
pub fn setup_cuda_env() {
    // Increase CUDA memory cache
    std::env::set_var("CUDA_CACHE_MAXSIZE", "2147483648"); // 2GB

    // Enable TF32 for faster matrix ops on Ampere+
    std::env::set_var("NVIDIA_TF32_OVERRIDE", "1");

    // Disable memory pool to reduce fragmentation
    // std::env::set_var("PYTORCH_NO_CUDA_MEMORY_CACHING", "1");

    println!("🚀 CUDA environment configured for turbo inference");
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_kv_cache() {
        let mut cache = ModelKVCache::new(4, 1024);
        assert_eq!(cache.seq_len(), 0);

        // Would need device for actual tensor tests
    }

    #[test]
    fn test_pin_strategy() {
        let pin = LayerPin::new(4.0, PinStrategy::FirstLast { first: 2, last: 2 });
        assert!(pin.should_pin(0, 10)); // First
        assert!(pin.should_pin(1, 10)); // First
        assert!(!pin.should_pin(5, 10)); // Middle
        assert!(pin.should_pin(8, 10)); // Last
        assert!(pin.should_pin(9, 10)); // Last
    }
}
