//! Python bindings for DensityClassifier

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use numpy::{PyReadonlyArray2, PyUntypedArrayMethods};
use arrow::array::{Array, Float32Array, FixedSizeListArray};
use arrow::pyarrow::FromPyArrow;
use dyf_core::{DensityClassifier, DensityReport, BridgeAnalysis, BitDepthStats, analyze_bit_depths, select_optimal_bit_depth};

/// Python wrapper for DensityReport
#[pyclass]
#[derive(Clone)]
pub struct PyDensityReport {
    #[pyo3(get)]
    pub corpus_size: usize,
    #[pyo3(get)]
    pub num_buckets: usize,
    #[pyo3(get)]
    pub stage1_variance_explained: f32,
    #[pyo3(get)]
    pub mean_bucket_size: f32,
    #[pyo3(get)]
    pub median_bucket_size: usize,
    #[pyo3(get)]
    pub max_bucket_size: usize,
    #[pyo3(get)]
    pub mean_centroid_similarity: f32,
    #[pyo3(get)]
    pub mean_isolation_score: f32,
    #[pyo3(get)]
    pub mean_stability_score: f32,
}

impl From<DensityReport> for PyDensityReport {
    fn from(report: DensityReport) -> Self {
        PyDensityReport {
            corpus_size: report.corpus_size,
            num_buckets: report.num_buckets,
            stage1_variance_explained: report.stage1_variance_explained,
            mean_bucket_size: report.mean_bucket_size,
            median_bucket_size: report.median_bucket_size,
            max_bucket_size: report.max_bucket_size,
            mean_centroid_similarity: report.mean_centroid_similarity,
            mean_isolation_score: report.mean_isolation_score,
            mean_stability_score: report.mean_stability_score,
        }
    }
}

#[pymethods]
impl PyDensityReport {
    fn __repr__(&self) -> String {
        format!(
            "DensityReport(corpus={}, buckets={}, mean_bucket={:.1})",
            self.corpus_size, self.num_buckets, self.mean_bucket_size
        )
    }

    fn __str__(&self) -> String {
        format!(
            "Corpus: {} items\n  Buckets: {}\n  Mean bucket size: {:.1}\n  Median bucket size: {}\n  Max bucket size: {}\n  Mean centroid similarity: {:.3}\n  Mean isolation score: {:.3}\n  Mean stability score: {:.3}\n  PCA variance explained: {:.1}%",
            self.corpus_size,
            self.num_buckets,
            self.mean_bucket_size,
            self.median_bucket_size,
            self.max_bucket_size,
            self.mean_centroid_similarity,
            self.mean_isolation_score,
            self.mean_stability_score,
            self.stage1_variance_explained * 100.0,
        )
    }
}

/// Python wrapper for BridgeAnalysis
#[pyclass]
#[derive(Clone)]
pub struct PyBridgeAnalysis {
    /// Indices of bridge items (low centroid similarity)
    #[pyo3(get)]
    pub bridge_indices: Vec<usize>,
    /// Unique bucket IDs in order
    #[pyo3(get)]
    pub bucket_ids: Vec<u64>,
    /// Adjacency matrix: flattened n_buckets x n_buckets, bridges connecting bucket pairs
    #[pyo3(get)]
    pub adjacency_matrix: Vec<u32>,
    /// Number of unique buckets
    #[pyo3(get)]
    pub n_buckets: usize,
    /// Threshold used for bridge detection
    #[pyo3(get)]
    pub bridge_threshold: f32,
    /// For each bridge: (item_idx, primary_bucket, list of connected_buckets)
    bridge_connections: Vec<(usize, u64, Vec<u64>)>,
}

impl From<BridgeAnalysis> for PyBridgeAnalysis {
    fn from(analysis: BridgeAnalysis) -> Self {
        PyBridgeAnalysis {
            bridge_indices: analysis.bridge_indices,
            bucket_ids: analysis.bucket_ids,
            adjacency_matrix: analysis.adjacency_matrix,
            n_buckets: analysis.n_buckets,
            bridge_threshold: analysis.bridge_threshold,
            bridge_connections: analysis.bridge_connections,
        }
    }
}

#[pymethods]
impl PyBridgeAnalysis {
    fn __repr__(&self) -> String {
        let total_edges: u32 = self.adjacency_matrix.iter().sum();
        format!(
            "BridgeAnalysis(bridges={}, buckets={}, edges={})",
            self.bridge_indices.len(),
            self.n_buckets,
            total_edges / 2  // symmetric
        )
    }

    fn __str__(&self) -> String {
        let total_edges: u32 = self.adjacency_matrix.iter().sum();
        let connected_pairs = self.adjacency_matrix.iter().filter(|&&x| x > 0).count() / 2;
        format!(
            "Bridge Analysis:\n  Bridges: {} items\n  Buckets: {}\n  Connected pairs: {}\n  Total bridge connections: {}\n  Bridge threshold: {:.2}",
            self.bridge_indices.len(),
            self.n_buckets,
            connected_pairs,
            total_edges / 2,
            self.bridge_threshold,
        )
    }

    /// Get connection info for a specific bridge by its index in bridge_indices
    fn get_bridge_connections(&self, bridge_idx: usize) -> PyResult<(usize, u64, Vec<u64>)> {
        if bridge_idx >= self.bridge_connections.len() {
            return Err(PyValueError::new_err(format!(
                "Bridge index {} out of range (0-{})",
                bridge_idx,
                self.bridge_connections.len().saturating_sub(1)
            )));
        }
        Ok(self.bridge_connections[bridge_idx].clone())
    }

    /// Get all bridges that connect two specific buckets
    fn bridges_between(&self, bucket_a: u64, bucket_b: u64) -> Vec<usize> {
        self.bridge_connections
            .iter()
            .filter_map(|(item_idx, primary, connected)| {
                // Check if this bridge connects bucket_a and bucket_b
                let connects_a_to_b = *primary == bucket_a && connected.contains(&bucket_b);
                let connects_b_to_a = *primary == bucket_b && connected.contains(&bucket_a);
                if connects_a_to_b || connects_b_to_a {
                    Some(*item_idx)
                } else {
                    None
                }
            })
            .collect()
    }

    /// Get the bucket pairs with the most bridges connecting them
    fn top_connected_pairs(&self, top_k: usize) -> Vec<(u64, u64, u32)> {
        let mut pairs: Vec<(u64, u64, u32)> = Vec::new();
        for i in 0..self.n_buckets {
            for j in (i + 1)..self.n_buckets {
                let count = self.adjacency_matrix[i * self.n_buckets + j];
                if count > 0 {
                    pairs.push((self.bucket_ids[i], self.bucket_ids[j], count));
                }
            }
        }
        pairs.sort_by(|a, b| b.2.cmp(&a.2));
        pairs.truncate(top_k);
        pairs
    }
}

/// Density Classifier using PCA-based LSH
///
/// Returns raw density metrics per item - classification is left to the caller.
///
/// Per-item metrics:
/// - bucket_id: LSH bucket assignment
/// - bucket_size: Number of items in the bucket
/// - centroid_similarity: Cosine similarity to bucket centroid (0-1)
/// - isolation_score: How isolated the item is (top_k_sim - median_sim)
/// - stability_score: How stable bucket assignment is across multiple seeds (0-1)
///
/// Example:
/// ```python
/// from dyf_rs import DensityClassifier
///
/// # Create classifier
/// classifier = DensityClassifier(
///     embedding_dim=384,
///     num_bits=14,
///     seed=31,
///     num_stability_seeds=3  # default
/// )
///
/// # Fit on embeddings (numpy array)
/// classifier.fit(embeddings)
///
/// # Get raw metrics
/// bucket_sizes = classifier.get_bucket_sizes()
/// centroid_sims = classifier.get_centroid_similarities()
/// isolation_scores = classifier.get_isolation_scores()
/// stability_scores = classifier.get_stability_scores()
/// report = classifier.report()
/// ```
#[pyclass]
pub struct PyDensityClassifier {
    classifier: DensityClassifier,
}

#[pymethods]
impl PyDensityClassifier {
    /// Create new density classifier
    ///
    /// # Arguments
    /// * `embedding_dim` - Dimensionality of embeddings
    /// * `num_bits` - Bits for PCA LSH (default: 14)
    /// * `seed` - Random seed (default: 31)
    /// * `num_stability_seeds` - Number of seeds for stability scoring (default: 3)
    #[new]
    #[pyo3(signature = (embedding_dim, num_bits=14, seed=31, num_stability_seeds=3))]
    fn new(
        embedding_dim: usize,
        num_bits: usize,
        seed: u64,
        num_stability_seeds: usize,
    ) -> Self {
        PyDensityClassifier {
            classifier: DensityClassifier::new(embedding_dim, num_bits, seed, num_stability_seeds),
        }
    }

    /// Fit the classifier on embeddings (numpy array - FAST)
    ///
    /// # Arguments
    /// * `embeddings` - 2D numpy array of shape (n_samples, embedding_dim), dtype float32
    ///
    /// # Returns
    /// Self for chaining
    ///
    /// This method accepts numpy arrays directly and passes the raw data slice to Rust,
    /// avoiding all Python-side conversion overhead.
    fn fit(&mut self, embeddings: PyReadonlyArray2<f32>) -> PyResult<()> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim,
                dim
            )));
        }

        // Use fit_flat for contiguous arrays (zero-copy path)
        if let Ok(slice) = embeddings.as_slice() {
            // Fast path: pass raw slice directly to Rust
            self.classifier.fit_flat(slice, n_samples, dim);
        } else {
            // Non-contiguous array - need to copy to contiguous buffer
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            self.classifier.fit_flat(&flat, n_samples, dim);
        }

        Ok(())
    }

    /// Ensemble fit: use consensus voting across multiple seeds
    ///
    /// Runs PCA-LSH with multiple seeds and assigns each item to
    /// its most common bucket (majority vote). Reduces boundary noise.
    ///
    /// Returns number of items where consensus differed from primary seed.
    #[pyo3(signature = (embeddings, num_seeds=5))]
    fn fit_ensemble(&mut self, embeddings: PyReadonlyArray2<f32>, num_seeds: usize) -> PyResult<usize> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.fit_ensemble_flat(slice, n_samples, dim, num_seeds))
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.fit_ensemble_flat(&flat, n_samples, dim, num_seeds))
        }
    }

    /// Recursive density-based splitting
    ///
    /// Subdivides dense buckets recursively. Sparse regions stop early,
    /// dense regions get more splits. Adaptive resolution.
    ///
    /// # Arguments
    /// * `embeddings` - 2D numpy array
    /// * `bits_per_level` - Bits at each recursion level (default: 4)
    /// * `max_depth` - Maximum recursion depth (default: 4)
    /// * `min_bucket_size` - Stop splitting below this (default: 20)
    ///
    /// # Example
    /// ```python
    /// classifier = DensityClassifier(embedding_dim=384)
    /// classifier.fit_recursive(embeddings, bits_per_level=4, max_depth=4, min_bucket_size=20)
    /// ```
    #[pyo3(signature = (embeddings, bits_per_level=4, max_depth=4, min_bucket_size=20))]
    fn fit_recursive(
        &mut self,
        embeddings: PyReadonlyArray2<f32>,
        bits_per_level: usize,
        max_depth: usize,
        min_bucket_size: usize,
    ) -> PyResult<()> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            self.classifier.fit_recursive_flat(slice, n_samples, dim, bits_per_level, max_depth, min_bucket_size);
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            self.classifier.fit_recursive_flat(&flat, n_samples, dim, bits_per_level, max_depth, min_bucket_size);
        }

        Ok(())
    }

    /// ITQ fit: Iterative Quantization for better hashing
    ///
    /// Learns a rotation matrix that minimizes quantization error when binarizing.
    /// Typically gives 5-15% improvement over raw PCA-LSH.
    ///
    /// # Arguments
    /// * `embeddings` - 2D numpy array of shape (n_samples, embedding_dim)
    /// * `max_iterations` - Number of ITQ iterations (default: 50)
    ///
    /// # Example
    /// ```python
    /// classifier = DensityClassifier(embedding_dim=384, num_bits=10)
    /// classifier.fit_itq(embeddings, max_iterations=50)
    /// ```
    #[pyo3(signature = (embeddings, max_iterations=50))]
    fn fit_itq(&mut self, embeddings: PyReadonlyArray2<f32>, max_iterations: usize) -> PyResult<()> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            self.classifier.fit_itq_flat(slice, n_samples, dim, max_iterations);
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            self.classifier.fit_itq_flat(&flat, n_samples, dim, max_iterations);
        }

        Ok(())
    }

    /// Hierarchical fit: coarse global hash + fine region-specific hash
    ///
    /// Stage 1 (Coarse): Global PCA on all items → coarse_bits hyperplanes
    /// Stage 2 (Fine): Per-region PCA on items in each coarse bucket → fine_bits hyperplanes
    ///
    /// Final bucket ID combines both: (coarse_id << fine_bits) | fine_id
    ///
    /// This captures both global structure (coarse) and local structure (fine),
    /// improving centroid similarity and NN recall over flat LSH.
    ///
    /// # Arguments
    /// * `embeddings` - 2D numpy array of shape (n_samples, embedding_dim)
    /// * `coarse_bits` - Bits for global hash (default: 6)
    /// * `fine_bits` - Bits for per-region hash (default: 4)
    ///
    /// # Example
    /// ```python
    /// classifier = DensityClassifier(embedding_dim=384)
    /// classifier.fit_hierarchical(embeddings, coarse_bits=6, fine_bits=4)
    /// # Total 10 bits: ~1024 potential buckets
    /// ```
    #[pyo3(signature = (embeddings, coarse_bits=6, fine_bits=4))]
    fn fit_hierarchical(&mut self, embeddings: PyReadonlyArray2<f32>, coarse_bits: usize, fine_bits: usize) -> PyResult<()> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            self.classifier.fit_hierarchical_flat(slice, n_samples, dim, coarse_bits, fine_bits);
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            self.classifier.fit_hierarchical_flat(&flat, n_samples, dim, coarse_bits, fine_bits);
        }

        Ok(())
    }

    /// Iterative fit: refine hyperplanes through multiple PCA iterations
    ///
    /// Each iteration:
    /// 1. Hash items with current hyperplanes
    /// 2. Compute bucket centroids
    /// 3. PCA on centroids → new hyperplanes
    /// 4. Repeat until convergence or max_iterations
    ///
    /// Returns (iterations_run, items_changed_last_iter)
    #[pyo3(signature = (embeddings, max_iterations=10))]
    fn fit_iterative(&mut self, embeddings: PyReadonlyArray2<f32>, max_iterations: usize) -> PyResult<(usize, usize)> {
        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.fit_iterative_flat(slice, n_samples, dim, max_iterations))
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.fit_iterative_flat(&flat, n_samples, dim, max_iterations))
        }
    }

    /// Fit the classifier on embeddings (list of lists - SLOW)
    ///
    /// # Arguments
    /// * `embeddings` - List of embedding vectors (list of lists)
    ///
    /// Use fit() with numpy arrays for better performance.
    fn fit_list(&mut self, embeddings: Vec<Vec<f32>>) -> PyResult<()> {
        if embeddings.is_empty() {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if embeddings[0].len() != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim,
                embeddings[0].len()
            )));
        }

        self.classifier.fit(&embeddings);
        Ok(())
    }

    /// Fit the classifier on embeddings (PyArrow FixedSizeListArray - ZERO COPY)
    ///
    /// # Arguments
    /// * `embeddings` - PyArrow FixedSizeListArray of float32, shape (n_samples, embedding_dim)
    ///
    /// This is the fastest path - zero-copy access to Arrow buffers.
    ///
    /// Example:
    /// ```python
    /// import pyarrow as pa
    /// flat = pa.array(embeddings.flatten(), type=pa.float32())
    /// arrow_emb = pa.FixedSizeListArray.from_arrays(flat, embedding_dim)
    /// classifier.fit_arrow(arrow_emb)
    /// ```
    fn fit_arrow(&mut self, py: Python<'_>, embeddings: PyObject) -> PyResult<()> {
        // Convert PyArrow array to Rust Arrow array using FFI
        let array = arrow::array::ArrayData::from_pyarrow_bound(embeddings.bind(py))
            .map_err(|e| PyValueError::new_err(format!("Failed to convert PyArrow array: {}", e)))?;

        let array: std::sync::Arc<dyn Array> = arrow::array::make_array(array);

        // Cast to FixedSizeListArray
        let list_array = array
            .as_any()
            .downcast_ref::<FixedSizeListArray>()
            .ok_or_else(|| PyValueError::new_err(
                "Expected FixedSizeListArray. Use pa.FixedSizeListArray.from_arrays(flat_data, embedding_dim)"
            ))?;

        let n_samples = list_array.len();
        let dim = list_array.value_length() as usize;

        if n_samples == 0 {
            return Err(PyValueError::new_err("Embeddings cannot be empty"));
        }

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim,
                dim
            )));
        }

        // Get the underlying float32 values - this is zero-copy!
        let values = list_array.values();
        let float_array = values
            .as_any()
            .downcast_ref::<Float32Array>()
            .ok_or_else(|| PyValueError::new_err("Expected Float32 values"))?;

        // Get slice of the underlying buffer
        let data: &[f32] = float_array.values();

        // Call fit_flat with the raw slice
        self.classifier.fit_flat(data, n_samples, dim);
        Ok(())
    }

    /// Get bucket IDs for all items
    fn get_bucket_ids(&self) -> PyResult<Vec<u64>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_bucket_ids().to_vec())
    }

    /// Get bucket ID for a single item
    fn get_bucket_id(&self, idx: usize) -> PyResult<Option<u64>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_bucket_id(idx))
    }

    /// Get bucket sizes for all items (number of items in each item's bucket)
    fn get_bucket_sizes(&self) -> PyResult<Vec<u32>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_bucket_sizes().to_vec())
    }

    /// Get centroid similarities for all items (0-1)
    fn get_centroid_similarities(&self) -> PyResult<Vec<f32>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_centroid_similarities().to_vec())
    }

    /// Get isolation scores for all items
    fn get_isolation_scores(&self) -> PyResult<Vec<f32>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_isolation_scores().to_vec())
    }

    /// Get stability scores for all items (0-1, higher = more stable)
    fn get_stability_scores(&self) -> PyResult<Vec<f32>> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.get_stability_scores().to_vec())
    }

    /// Get classification report
    fn report(&self) -> PyResult<PyDensityReport> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }
        Ok(self.classifier.report().into())
    }

    /// Check if classifier is fitted
    fn is_fitted(&self) -> bool {
        self.classifier.is_fitted()
    }

    /// Voronoi refinement: reassign items to nearest centroid among Hamming neighbors
    ///
    /// This refines LSH bucket assignments by checking if a nearby bucket's centroid
    /// is actually closer. Only checks buckets within `max_hamming_distance` bits
    /// of the current bucket (cheap Voronoi).
    ///
    /// # Arguments
    /// * `embeddings` - Same embeddings used in fit() - required for centroid computation
    /// * `max_hamming_distance` - Maximum bit difference to consider as neighbor (default: 2)
    ///
    /// # Returns
    /// Number of items reassigned to different buckets
    ///
    /// # Example
    /// ```python
    /// classifier.fit(embeddings)
    /// print(f"Before: {classifier.report()}")
    /// reassigned = classifier.voronoi_refine(embeddings, max_hamming_distance=2)
    /// print(f"Reassigned {reassigned} items")
    /// print(f"After: {classifier.report()}")
    /// ```
    /// Adaptive Voronoi refinement: search radius based on item confidence
    ///
    /// Low-confidence items (low centroid_similarity) get wider Hamming search.
    /// - sim < 0.5: Hamming ≤ 3 (wide search)
    /// - sim 0.5-0.7: Hamming ≤ 2 (medium)
    /// - sim > 0.7: Hamming ≤ 1 (narrow)
    fn voronoi_refine_adaptive(&mut self, embeddings: PyReadonlyArray2<f32>) -> PyResult<usize> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }

        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.voronoi_refine_adaptive_flat(slice, n_samples, dim))
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.voronoi_refine_adaptive_flat(&flat, n_samples, dim))
        }
    }

    #[pyo3(signature = (embeddings, max_hamming_distance=2))]
    fn voronoi_refine(&mut self, embeddings: PyReadonlyArray2<f32>, max_hamming_distance: u32) -> PyResult<usize> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }

        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim,
                dim
            )));
        }

        // Use flat data for the refinement
        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.voronoi_refine_flat(slice, n_samples, dim, max_hamming_distance))
        } else {
            // Non-contiguous - copy to contiguous buffer
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.voronoi_refine_flat(&flat, n_samples, dim, max_hamming_distance))
        }
    }

    /// Margin-based selective Voronoi refinement
    ///
    /// Only refines items that are close to hyperplane boundaries (low margin).
    /// Items with high confidence (far from all boundaries) are skipped.
    ///
    /// This is more efficient than full Voronoi when most items are well-assigned.
    ///
    /// # Arguments
    /// * `embeddings` - Same embeddings used in fit()
    /// * `margin_threshold` - Items with margin below this are refined (default: 0.1)
    /// * `max_hamming_distance` - Hamming radius for neighbor search (default: 2)
    ///
    /// # Returns
    /// Tuple of (items_checked, items_reassigned)
    ///
    /// # Example
    /// ```python
    /// classifier.fit(embeddings)
    /// checked, moved = classifier.voronoi_refine_margin(embeddings, margin_threshold=0.1)
    /// print(f"Checked {checked} low-confidence items, moved {moved}")
    /// ```
    #[pyo3(signature = (embeddings, margin_threshold=0.1, max_hamming_distance=2))]
    fn voronoi_refine_margin(
        &mut self,
        embeddings: PyReadonlyArray2<f32>,
        margin_threshold: f32,
        max_hamming_distance: u32,
    ) -> PyResult<(usize, usize)> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }

        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.voronoi_refine_margin_flat(slice, n_samples, dim, margin_threshold, max_hamming_distance))
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.voronoi_refine_margin_flat(&flat, n_samples, dim, margin_threshold, max_hamming_distance))
        }
    }

    /// Analyze bridge items to discover region connectivity
    ///
    /// Bridges are items with low centroid similarity - they sit between regions.
    /// This analysis finds which buckets are connected through these bridge items.
    ///
    /// # Arguments
    /// * `embeddings` - Same embeddings used in fit()
    /// * `bridge_threshold` - Items with centroid_sim below this are bridges (default: 0.5)
    /// * `connection_threshold` - Min similarity to consider connected to a bucket (default: 0.3)
    ///
    /// # Returns
    /// BridgeAnalysis with connectivity information
    ///
    /// # Example
    /// ```python
    /// classifier.fit(embeddings)
    /// analysis = classifier.analyze_bridges(embeddings, bridge_threshold=0.5)
    /// print(analysis)  # Shows bridge count, connected pairs
    /// top_pairs = analysis.top_connected_pairs(10)  # Most connected bucket pairs
    /// ```
    #[pyo3(signature = (embeddings, bridge_threshold=0.5, connection_threshold=0.3))]
    fn analyze_bridges(
        &self,
        embeddings: PyReadonlyArray2<f32>,
        bridge_threshold: f32,
        connection_threshold: f32,
    ) -> PyResult<PyBridgeAnalysis> {
        if !self.classifier.is_fitted() {
            return Err(PyValueError::new_err("Classifier not fitted. Call fit() first."));
        }

        let shape = embeddings.shape();
        let n_samples = shape[0];
        let dim = shape[1];

        let expected_dim = self.classifier.embedding_dim();
        if dim != expected_dim {
            return Err(PyValueError::new_err(format!(
                "Embedding dimension mismatch: expected {}, got {}",
                expected_dim, dim
            )));
        }

        if let Ok(slice) = embeddings.as_slice() {
            Ok(self.classifier.analyze_bridges_flat(slice, n_samples, dim, bridge_threshold, connection_threshold).into())
        } else {
            let array = embeddings.as_array();
            let flat: Vec<f32> = (0..n_samples)
                .flat_map(|i| array.row(i).to_vec())
                .collect();
            Ok(self.classifier.analyze_bridges_flat(&flat, n_samples, dim, bridge_threshold, connection_threshold).into())
        }
    }

    fn __repr__(&self) -> String {
        if self.classifier.is_fitted() {
            let report = self.classifier.report();
            format!(
                "DensityClassifier(fitted=True, corpus={}, buckets={}, mean_bucket={:.1})",
                report.corpus_size, report.num_buckets, report.mean_bucket_size
            )
        } else {
            "DensityClassifier(fitted=False)".to_string()
        }
    }
}

/// Statistics for a single bit depth analysis
#[pyclass]
#[derive(Clone)]
pub struct PyBitDepthStats {
    #[pyo3(get)]
    pub bits: usize,
    #[pyo3(get)]
    pub num_buckets: usize,
    #[pyo3(get)]
    pub max_bucket_size: usize,
    #[pyo3(get)]
    pub median_bucket_size: usize,
    #[pyo3(get)]
    pub min_bucket_size: usize,
    #[pyo3(get)]
    pub mean_bucket_size: f32,
    #[pyo3(get)]
    pub buckets_over_1000: usize,
    #[pyo3(get)]
    pub buckets_under_10: usize,
}

impl From<BitDepthStats> for PyBitDepthStats {
    fn from(stats: BitDepthStats) -> Self {
        PyBitDepthStats {
            bits: stats.bits,
            num_buckets: stats.num_buckets,
            max_bucket_size: stats.max_bucket_size,
            median_bucket_size: stats.median_bucket_size,
            min_bucket_size: stats.min_bucket_size,
            mean_bucket_size: stats.mean_bucket_size,
            buckets_over_1000: stats.buckets_over_1000,
            buckets_under_10: stats.buckets_under_10,
        }
    }
}

#[pymethods]
impl PyBitDepthStats {
    fn __repr__(&self) -> String {
        format!(
            "BitDepthStats(bits={}, buckets={}, mean={:.1}, max={})",
            self.bits, self.num_buckets, self.mean_bucket_size, self.max_bucket_size
        )
    }

    fn __str__(&self) -> String {
        format!(
            "Bits: {}\n  Buckets: {}\n  Mean: {:.1}, Median: {}, Max: {}, Min: {}\n  >1000: {}, <10: {}",
            self.bits,
            self.num_buckets,
            self.mean_bucket_size, self.median_bucket_size, self.max_bucket_size, self.min_bucket_size,
            self.buckets_over_1000, self.buckets_under_10
        )
    }
}

/// Analyze multiple bit depths to find optimal LSH configuration
///
/// # Arguments
/// * `embeddings` - 2D numpy array of shape (n_samples, embedding_dim), dtype float32
/// * `min_bits` - Minimum bit depth to test (default: 8)
/// * `max_bits` - Maximum bit depth to test (default: 18)
/// * `seed` - Random seed (default: 42)
///
/// # Returns
/// List of BitDepthStats for each bit depth tested
#[pyfunction]
#[pyo3(signature = (embeddings, min_bits=8, max_bits=18, seed=42))]
pub fn py_analyze_bit_depths(
    embeddings: PyReadonlyArray2<f32>,
    min_bits: usize,
    max_bits: usize,
    seed: u64,
) -> PyResult<Vec<PyBitDepthStats>> {
    let shape = embeddings.shape();
    let n_samples = shape[0];
    let dim = shape[1];

    if n_samples == 0 {
        return Err(PyValueError::new_err("Embeddings cannot be empty"));
    }

    // Get data slice
    let data = embeddings.as_slice()
        .map_err(|_| PyValueError::new_err("Array must be contiguous"))?;

    let stats = analyze_bit_depths(data, n_samples, dim, min_bits..max_bits, seed);
    Ok(stats.into_iter().map(|s| s.into()).collect())
}

/// Select optimal bit depth based on heuristics
///
/// # Arguments
/// * `stats` - List of BitDepthStats from analyze_bit_depths
/// * `target_mean_bucket` - Target mean bucket size (default: 50.0)
/// * `max_bucket` - Maximum acceptable bucket size (default: 2000)
///
/// # Returns
/// Optimal bit depth, or None if no suitable depth found
#[pyfunction]
#[pyo3(signature = (stats, target_mean_bucket=50.0, max_bucket=2000))]
pub fn py_select_optimal_bit_depth(
    stats: Vec<PyBitDepthStats>,
    target_mean_bucket: f32,
    max_bucket: usize,
) -> Option<usize> {
    // Convert back to Rust structs
    let rust_stats: Vec<BitDepthStats> = stats.into_iter().map(|s| BitDepthStats {
        bits: s.bits,
        num_buckets: s.num_buckets,
        max_bucket_size: s.max_bucket_size,
        median_bucket_size: s.median_bucket_size,
        min_bucket_size: s.min_bucket_size,
        mean_bucket_size: s.mean_bucket_size,
        buckets_over_1000: s.buckets_over_1000,
        buckets_under_10: s.buckets_under_10,
    }).collect();

    select_optimal_bit_depth(&rust_stats, target_mean_bucket, max_bucket)
}
