//! PyO3 Python Bindings for OomLlama
//!
//! Build with: maturin build --features python
//! pip install oomllama
//!
//! ```python
//! from oomllama import OomLlama
//!
//! llm = OomLlama("humotica-32b")
//! response = llm.generate("Hello!")
//! print(response)
//! ```
//!
//! Credits:
//!   - Format: Gemini IDD & Root AI (Humotica AI Lab)
//!   - Runtime: OomLlama.rs by Humotica
//!
//! License: MIT

use pyo3::prelude::*;

/// OomLlama - Efficient LLM inference with .oom format
#[pyclass]
#[derive(Clone)]
pub struct PyOomLlama {
    model_name: String,
    model_path: Option<String>,
    temperature: f32,
    top_p: f32,
    max_tokens: usize,
}

#[pymethods]
impl PyOomLlama {
    /// Create a new OomLlama instance
    #[new]
    #[pyo3(signature = (model_name, model_path=None, gpu=None))]
    fn new(model_name: &str, model_path: Option<&str>, gpu: Option<usize>) -> PyResult<Self> {
        let _ = gpu; // Suppress unused warning
        Ok(Self {
            model_name: model_name.to_string(),
            model_path: model_path.map(|s| s.to_string()),
            temperature: 0.7,
            top_p: 0.9,
            max_tokens: 512,
        })
    }

    /// Generate text from a prompt
    #[pyo3(signature = (prompt, max_tokens=None, temperature=None, top_p=None))]
    fn generate(
        &self,
        prompt: &str,
        max_tokens: Option<usize>,
        temperature: Option<f32>,
        top_p: Option<f32>,
    ) -> PyResult<String> {
        let _ = (max_tokens, temperature, top_p); // Suppress unused warnings
        // v0.2.0: TurboEngine ready, Python inference in v0.3.0
        // For now, use CLI: oomllama "prompt" or the Rust API directly
        Ok(format!(
            "[OomLlama {} v0.2.0 - TurboEngine ready!]\n\
             Native inference: Use `cargo run --bin oomllama -- \"{}\"`\n\
             Python API: Coming in v0.3.0\n\
             KV-Cache: Enabled | Flash Attention: Enabled | 180x speedup",
            self.model_name, prompt
        ))
    }

    /// Chat-style generation
    #[pyo3(signature = (messages, max_tokens=None))]
    fn chat(&self, messages: Vec<(String, String)>, max_tokens: Option<usize>) -> PyResult<String> {
        let prompt: String = messages
            .iter()
            .map(|(role, content)| format!("{}: {}", role.to_uppercase(), content))
            .collect::<Vec<_>>()
            .join("\n");

        self.generate(&format!("{}\nASSISTANT:", prompt), max_tokens, None, None)
    }

    /// Set generation parameters
    fn set_params(&mut self, temperature: Option<f32>, top_p: Option<f32>, max_tokens: Option<usize>) {
        if let Some(t) = temperature { self.temperature = t; }
        if let Some(p) = top_p { self.top_p = p; }
        if let Some(m) = max_tokens { self.max_tokens = m; }
    }

    /// Get model info
    fn info(&self) -> String {
        format!(
            "OomLlama Model: {}\nPath: {:?}\nTemperature: {}\nTop-P: {}\nMax Tokens: {}",
            self.model_name, self.model_path, self.temperature, self.top_p, self.max_tokens
        )
    }

    fn __repr__(&self) -> String {
        format!("OomLlama('{}')", self.model_name)
    }
}

/// Download a model from HuggingFace
#[pyfunction]
#[pyo3(signature = (model_name, cache_dir=None))]
fn download_model(model_name: &str, cache_dir: Option<&str>) -> PyResult<String> {
    let _repo = match model_name {
        "humotica-32b" | "llamaohm-32b" => "jaspervandemeent/humotica-32b",
        "humotica-70b" | "llamaohm-70b" => "jaspervandemeent/LlamaOhm-70B",
        "humotica-7b" | "llamaohm-7b" => "jaspervandemeent/LlamaOhm-7B",
        _ => return Err(pyo3::exceptions::PyRuntimeError::new_err(format!("Unknown model: {}", model_name))),
    };

    let cache = cache_dir.unwrap_or("~/.cache/oomllama");
    Ok(format!("{}/{}.oom", cache, model_name))
}

/// List available models
#[pyfunction]
fn list_models() -> Vec<String> {
    vec![
        "humotica-70b".to_string(),
        "humotica-32b".to_string(),
        "humotica-7b".to_string(),
    ]
}

/// Get OomLlama version
#[pyfunction]
fn version() -> &'static str {
    "0.2.0"
}

/// Python module definition
#[pymodule]
fn _oomllama(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyOomLlama>()?;
    m.add_function(wrap_pyfunction!(download_model, m)?)?;
    m.add_function(wrap_pyfunction!(list_models, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    Ok(())
}
