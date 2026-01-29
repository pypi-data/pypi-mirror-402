//! Density Classifier: Discover structure in embedding spaces
//!
//! Returns raw density metrics per item - classification is left to the caller.
//!
//! Outputs per item:
//! - bucket_id: LSH bucket assignment
//! - bucket_size: Number of items in the bucket
//! - centroid_similarity: Cosine similarity to bucket centroid (0-1)
//! - isolation_score: How isolated the item is (top_k_sim - median_sim)
//! - stability_score: How stable bucket assignment is across multiple seeds (0-1)

use nalgebra::DMatrix;
use ndarray::{Array2, ArrayView2};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use rayon::prelude::*;
use std::collections::HashMap;

// Link BLAS
extern crate blas_src;

/// Bridge analysis results - reveals region connectivity structure
#[derive(Debug, Clone)]
pub struct BridgeAnalysis {
    /// Indices of bridge items (low centroid similarity)
    pub bridge_indices: Vec<usize>,
    /// For each bridge: (item_idx, primary_bucket, connected_buckets)
    pub bridge_connections: Vec<(usize, u64, Vec<u64>)>,
    /// Unique bucket IDs in order
    pub bucket_ids: Vec<u64>,
    /// Adjacency matrix: bucket_i -> bucket_j -> bridge count
    /// Flattened as Vec of length n_buckets * n_buckets
    pub adjacency_matrix: Vec<u32>,
    /// Number of unique buckets
    pub n_buckets: usize,
    /// Threshold used for bridge detection
    pub bridge_threshold: f32,
}

/// Report from density classification
#[derive(Debug, Clone)]
pub struct DensityReport {
    pub corpus_size: usize,
    pub num_buckets: usize,
    pub stage1_variance_explained: f32,
    pub mean_bucket_size: f32,
    pub median_bucket_size: usize,
    pub max_bucket_size: usize,
    pub mean_centroid_similarity: f32,
    pub mean_isolation_score: f32,
    pub mean_stability_score: f32,
}

/// Statistics for a single bit depth analysis
#[derive(Debug, Clone)]
pub struct BitDepthStats {
    pub bits: usize,
    pub num_buckets: usize,
    pub max_bucket_size: usize,
    pub median_bucket_size: usize,
    pub min_bucket_size: usize,
    pub mean_bucket_size: f32,
    pub buckets_over_1000: usize,
    pub buckets_under_10: usize,
}

/// Analyze multiple bit depths to find optimal LSH configuration
pub fn analyze_bit_depths(
    data: &[f32],
    n_samples: usize,
    embedding_dim: usize,
    bit_range: std::ops::Range<usize>,
    seed: u64,
) -> Vec<BitDepthStats> {
    bit_range
        .map(|bits| {
            let mut classifier = DensityClassifier::new(embedding_dim, bits, seed, 3);
            classifier.fit_flat(data, n_samples, embedding_dim);

            let bucket_sizes = classifier.get_bucket_sizes();
            let mut unique_sizes: HashMap<u64, usize> = HashMap::new();
            for (&bid, &size) in classifier.bucket_ids.iter().zip(bucket_sizes.iter()) {
                unique_sizes.insert(bid, size as usize);
            }

            let mut sizes: Vec<usize> = unique_sizes.values().copied().collect();
            sizes.sort();

            let (max_sz, median_sz, min_sz) = if sizes.is_empty() {
                (0, 0, 0)
            } else {
                (sizes[sizes.len() - 1], sizes[sizes.len() / 2], sizes[0])
            };

            let mean_sz = if sizes.is_empty() {
                0.0
            } else {
                sizes.iter().sum::<usize>() as f32 / sizes.len() as f32
            };

            BitDepthStats {
                bits,
                num_buckets: unique_sizes.len(),
                max_bucket_size: max_sz,
                median_bucket_size: median_sz,
                min_bucket_size: min_sz,
                mean_bucket_size: mean_sz,
                buckets_over_1000: sizes.iter().filter(|&&s| s > 1000).count(),
                buckets_under_10: sizes.iter().filter(|&&s| s < 10).count(),
            }
        })
        .collect()
}

/// Select optimal bit depth based on heuristics
pub fn select_optimal_bit_depth(
    stats: &[BitDepthStats],
    target_mean_bucket: f32,
    max_bucket: usize,
) -> Option<usize> {
    // Find one that has reasonable mean bucket size and max bucket
    for s in stats {
        if s.mean_bucket_size >= target_mean_bucket && s.max_bucket_size <= max_bucket {
            return Some(s.bits);
        }
    }

    // Fallback: best trade-off
    stats
        .iter()
        .filter(|s| s.max_bucket_size <= max_bucket * 2)
        .min_by_key(|s| (s.mean_bucket_size - target_mean_bucket).abs() as usize)
        .map(|s| s.bits)
        .or_else(|| stats.first().map(|s| s.bits))
}

/// Density Classifier using PCA-based LSH
///
/// Returns raw metrics per item - no categorical classification.
pub struct DensityClassifier {
    // Configuration
    embedding_dim: usize,
    num_bits: usize,
    seed: u64,
    num_stability_seeds: usize,

    // PCA hyperplanes
    hyperplanes: Option<DMatrix<f32>>,

    // Per-item results
    bucket_ids: Vec<u64>,
    bucket_sizes: Vec<u32>,
    centroid_similarities: Vec<f32>,
    isolation_scores: Vec<f32>,
    stability_scores: Vec<f32>,

    // Stats
    stage1_variance: f32,
    num_buckets: usize,

    fitted: bool,
}

impl DensityClassifier {
    /// Create new density classifier
    ///
    /// # Arguments
    /// * `embedding_dim` - Dimensionality of embeddings
    /// * `num_bits` - Bits for PCA LSH (default: 14)
    /// * `seed` - Random seed
    /// * `num_stability_seeds` - Number of seeds for stability scoring (default: 3)
    pub fn new(embedding_dim: usize, num_bits: usize, seed: u64, num_stability_seeds: usize) -> Self {
        DensityClassifier {
            embedding_dim,
            num_bits,
            seed,
            num_stability_seeds,
            hyperplanes: None,
            bucket_ids: Vec::new(),
            bucket_sizes: Vec::new(),
            centroid_similarities: Vec::new(),
            isolation_scores: Vec::new(),
            stability_scores: Vec::new(),
            stage1_variance: 0.0,
            num_buckets: 0,
            fitted: false,
        }
    }

    /// Create with default parameters
    pub fn with_defaults(embedding_dim: usize) -> Self {
        Self::new(embedding_dim, 14, 31, 3)
    }

    /// Fit from a flat slice (zero-copy from numpy)
    pub fn fit_flat(&mut self, data: &[f32], n_samples: usize, dim: usize) -> &Self {
        if n_samples == 0 || dim != self.embedding_dim {
            self.fitted = true;
            return self;
        }

        // Normalize data into a flat buffer
        let mut normalized = vec![0.0f32; n_samples * dim];
        normalized
            .par_chunks_mut(dim)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * dim;
                let in_row = &data[start..start + dim];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        self.fit_internal_flat(&normalized, n_samples, dim)
    }

    /// Fit the density classifier on embeddings
    pub fn fit(&mut self, embeddings: &[Vec<f32>]) -> &Self {
        let n = embeddings.len();
        if n == 0 {
            self.fitted = true;
            return self;
        }

        // Normalize embeddings (parallel)
        let embeddings: Vec<Vec<f32>> = embeddings
            .par_iter()
            .map(|e| {
                let norm: f32 = e.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    e.iter().map(|x| x / norm).collect()
                } else {
                    e.clone()
                }
            })
            .collect();

        // Convert to flat
        let dim = embeddings[0].len();
        let mut flat = vec![0.0f32; n * dim];
        for (i, emb) in embeddings.iter().enumerate() {
            flat[i * dim..(i + 1) * dim].copy_from_slice(emb);
        }

        self.fit_internal_flat(&flat, n, dim)
    }

    /// Ensemble fit: use consensus voting across multiple seeds
    ///
    /// Runs PCA-LSH with multiple seeds and assigns each item to
    /// its most common bucket (majority vote). Reduces boundary noise.
    ///
    /// Returns number of items where consensus differed from primary seed.
    pub fn fit_ensemble_flat(&mut self, data: &[f32], n: usize, d: usize, num_seeds: usize) -> usize {
        if n == 0 || d != self.embedding_dim || num_seeds == 0 {
            self.fitted = true;
            return 0;
        }

        // Normalize data
        let mut normalized = vec![0.0f32; n * d];
        normalized
            .par_chunks_mut(d)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * d;
                let in_row = &data[start..start + d];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        // First, do standard PCA-LSH to get base hyperplanes
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed);
        let random_hp = self.generate_random_hyperplanes(&mut rng, self.num_bits);
        let random_hashes = self.hash_embeddings_flat(&normalized, n, d, &random_hp);
        let centroids = self.compute_all_centroids_flat(&normalized, n, d, &random_hashes, 2);
        let num_centroids = centroids.len() / d;

        let base_hp = if num_centroids > self.num_bits {
            let (hp, variance) = self.compute_pca_flat(&centroids, num_centroids, d, self.num_bits);
            self.stage1_variance = variance;
            hp
        } else {
            random_hp
        };

        // Run with base hyperplanes + perturbations
        let mut all_hashes: Vec<Vec<u64>> = Vec::with_capacity(num_seeds);

        for seed_idx in 0..num_seeds {
            let perturbed_hp = if seed_idx == 0 {
                // First seed uses exact base hyperplanes
                base_hp.clone()
            } else {
                // Perturb hyperplanes slightly (1% noise)
                let seed = self.seed + (seed_idx as u64 * 1000);
                let mut rng = ChaCha8Rng::seed_from_u64(seed);
                let mut hp = base_hp.clone();

                for i in 0..self.num_bits {
                    for j in 0..d {
                        hp[(i, j)] += rng.gen_range(-0.01f32..0.01f32);
                    }
                    // Re-normalize
                    let norm: f32 = (0..d).map(|j| hp[(i, j)].powi(2)).sum::<f32>().sqrt();
                    if norm > 0.0 {
                        for j in 0..d {
                            hp[(i, j)] /= norm;
                        }
                    }
                }
                hp
            };

            let hashes = self.hash_embeddings_flat(&normalized, n, d, &perturbed_hp);
            all_hashes.push(hashes);
        }

        let primary_hyperplanes = Some(base_hp);

        // Majority vote for each item
        let consensus_hashes: Vec<u64> = (0..n)
            .into_par_iter()
            .map(|i| {
                // Count votes for each bucket
                let mut votes: HashMap<u64, usize> = HashMap::new();
                for seed_hashes in &all_hashes {
                    *votes.entry(seed_hashes[i]).or_default() += 1;
                }

                // Find bucket with most votes
                votes
                    .into_iter()
                    .max_by_key(|(_, count)| *count)
                    .map(|(bucket, _)| bucket)
                    .unwrap_or(all_hashes[0][i])
            })
            .collect();

        // Count how many items differ from primary seed
        let changed = consensus_hashes
            .iter()
            .zip(all_hashes[0].iter())
            .filter(|(consensus, primary)| consensus != primary)
            .count();

        // Store results
        self.hyperplanes = primary_hyperplanes;
        self.bucket_ids = consensus_hashes;

        // Build bucket mapping and compute metrics
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in self.bucket_ids.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(&normalized, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &normalized[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Compute stability using the ensemble hashes we already have
        self.stability_scores = (0..n)
            .into_par_iter()
            .map(|i| {
                let mut buckets: Vec<u64> = all_hashes.iter().map(|h| h[i]).collect();
                buckets.sort();
                buckets.dedup();
                let unique_count = buckets.len();

                if num_seeds <= 1 {
                    1.0
                } else {
                    1.0 - (unique_count as f32 - 1.0) / (num_seeds as f32 - 1.0)
                }
            })
            .collect();

        // Compute isolation scores
        self.compute_isolation_scores_flat(&normalized, n, d, 10);

        self.fitted = true;
        changed
    }

    /// Iterative fit: refine hyperplanes by repeating PCA on centroids
    ///
    /// Each iteration:
    /// 1. Hash items with current hyperplanes
    /// 2. Compute bucket centroids
    /// 3. PCA on centroids → new hyperplanes
    /// 4. Repeat until convergence or max_iterations
    ///
    /// Returns (self, iterations_run, items_changed_last_iter)
    pub fn fit_iterative_flat(&mut self, data: &[f32], n: usize, d: usize, max_iterations: usize) -> (usize, usize) {
        if n == 0 || d != self.embedding_dim {
            self.fitted = true;
            return (0, 0);
        }

        // Normalize data
        let mut normalized = vec![0.0f32; n * d];
        normalized
            .par_chunks_mut(d)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * d;
                let in_row = &data[start..start + d];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        // Initial random hash
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed);
        let mut current_hp = self.generate_random_hyperplanes(&mut rng, self.num_bits);
        let mut current_hashes = self.hash_embeddings_flat(&normalized, n, d, &current_hp);

        let mut iterations = 0;
        let mut last_changed = n; // First iteration "changes" everything

        for iter in 0..max_iterations {
            // Compute centroids from current buckets
            let centroids = self.compute_all_centroids_flat(&normalized, n, d, &current_hashes, 2);
            let num_centroids = centroids.len() / d;

            if num_centroids <= self.num_bits {
                // Not enough centroids for PCA, stop iterating
                break;
            }

            // PCA on centroids → new hyperplanes
            let (pca_hp, variance) = self.compute_pca_flat(&centroids, num_centroids, d, self.num_bits);
            self.stage1_variance = variance;

            // Damped update: blend new hyperplanes with old (reduces oscillation)
            // First align signs (eigenvectors have arbitrary sign)
            let alpha = 0.5f32;
            let mut new_hp = DMatrix::<f32>::zeros(self.num_bits, d);
            for i in 0..self.num_bits {
                // Check if PCA hyperplane points same direction as current
                let dot: f32 = (0..d).map(|j| pca_hp[(i, j)] * current_hp[(i, j)]).sum();
                let sign = if dot >= 0.0 { 1.0f32 } else { -1.0f32 };

                // Blend with aligned sign
                for j in 0..d {
                    new_hp[(i, j)] = alpha * sign * pca_hp[(i, j)] + (1.0 - alpha) * current_hp[(i, j)];
                }
                // Re-normalize row
                let norm: f32 = (0..d).map(|j| new_hp[(i, j)].powi(2)).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for j in 0..d {
                        new_hp[(i, j)] /= norm;
                    }
                }
            }

            // Re-hash with blended hyperplanes
            let new_hashes = self.hash_embeddings_flat(&normalized, n, d, &new_hp);

            // Count how many items changed buckets
            let changed: usize = current_hashes
                .iter()
                .zip(new_hashes.iter())
                .filter(|(old, new)| old != new)
                .count();

            current_hp = new_hp;
            current_hashes = new_hashes;
            iterations = iter + 1;
            last_changed = changed;

            // Convergence check: if very few items moved, stop
            if changed < n / 100 {
                // Less than 1% changed
                break;
            }
        }

        // Store final hyperplanes and hashes
        self.hyperplanes = Some(current_hp);
        self.bucket_ids = current_hashes;

        // Build bucket mapping and compute metrics
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in self.bucket_ids.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(&normalized, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &normalized[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Compute isolation and stability scores
        self.compute_isolation_scores_flat(&normalized, n, d, 10);
        self.compute_stability_scores_flat(&normalized, n, d);

        self.fitted = true;
        (iterations, last_changed)
    }

    /// Internal fit implementation using flat slices
    fn fit_internal_flat(&mut self, data: &[f32], n: usize, d: usize) -> &Self {
        // Step 1: Random hash to get initial buckets for centroid computation
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed);
        let random_hp = self.generate_random_hyperplanes(&mut rng, self.num_bits);
        let random_hashes = self.hash_embeddings_flat(data, n, d, &random_hp);

        // Step 2: Compute bucket centroids
        let centroids = self.compute_all_centroids_flat(data, n, d, &random_hashes, 2);
        let num_centroids = centroids.len() / d;

        // Step 3: PCA on centroids
        let (pca_hp, variance) = if num_centroids > self.num_bits {
            self.compute_pca_flat(&centroids, num_centroids, d, self.num_bits)
        } else {
            (random_hp.clone(), 0.0)
        };
        self.hyperplanes = Some(pca_hp.clone());
        self.stage1_variance = variance;

        // Step 4: Re-hash with PCA hyperplanes
        let hashes = self.hash_embeddings_flat(data, n, d, &pca_hp);
        self.bucket_ids = hashes.clone();

        // Build bucket mapping
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in hashes.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Step 5: Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;

            // Compute centroid
            let centroid = self.compute_centroid_flat(data, d, indices);

            // Set bucket size and centroid similarity for each item
            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &data[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Step 6: Compute isolation scores
        self.compute_isolation_scores_flat(data, n, d, 10);

        // Step 7: Compute stability scores across multiple seeds
        self.compute_stability_scores_flat(data, n, d);

        self.fitted = true;
        self
    }

    /// Compute isolation score for each item
    /// isolation = mean(top_k similarities) - median(all similarities)
    fn compute_isolation_scores_flat(&mut self, data: &[f32], n: usize, d: usize, k: usize) {
        self.isolation_scores = vec![0.0f32; n];

        // For efficiency, sample the corpus for median computation
        let sample_size = 1000.min(n);
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed + 12345);
        let sample_indices: Vec<usize> = if n <= sample_size {
            (0..n).collect()
        } else {
            let mut indices: Vec<usize> = (0..n).collect();
            for i in 0..sample_size {
                let j = rng.gen_range(i..n);
                indices.swap(i, j);
            }
            indices[..sample_size].to_vec()
        };

        // Compute isolation scores in parallel
        self.isolation_scores = (0..n)
            .into_par_iter()
            .map(|i| {
                let row_i = &data[i * d..(i + 1) * d];

                // Compute similarities to sample
                let mut sims: Vec<f32> = sample_indices
                    .iter()
                    .filter(|&&j| j != i)
                    .map(|&j| {
                        let row_j = &data[j * d..(j + 1) * d];
                        self.cosine_similarity(row_i, row_j)
                    })
                    .collect();

                if sims.is_empty() {
                    return 0.0;
                }

                // Sort to get top-k and median
                sims.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));

                let top_k_mean: f32 = sims.iter().take(k).sum::<f32>() / k.min(sims.len()) as f32;
                let median = sims[sims.len() / 2];

                top_k_mean - median
            })
            .collect();
    }

    /// Compute stability score for each item across multiple seeds
    /// stability = 1 - (unique_buckets - 1) / (num_seeds - 1)
    /// 1.0 = same bucket in all seeds, 0.0 = different bucket in each seed
    fn compute_stability_scores_flat(&mut self, data: &[f32], n: usize, d: usize) {
        if self.num_stability_seeds <= 1 {
            // No stability computation with 0 or 1 seed
            self.stability_scores = vec![1.0f32; n];
            return;
        }

        // Compute bucket assignments for each seed
        // Start offset at 1 to avoid correlation with main seed's hyperplanes
        let mut all_hashes: Vec<Vec<u64>> = Vec::with_capacity(self.num_stability_seeds);

        for seed_idx in 0..self.num_stability_seeds {
            let seed = self.seed + ((seed_idx + 1) as u64 * 1000);

            // Generate random hyperplanes for this seed
            let mut rng = ChaCha8Rng::seed_from_u64(seed);
            let random_hp = self.generate_random_hyperplanes(&mut rng, self.num_bits);
            let random_hashes = self.hash_embeddings_flat(data, n, d, &random_hp);

            // Compute centroids for PCA
            let centroids = self.compute_all_centroids_flat(data, n, d, &random_hashes, 2);
            let num_centroids = centroids.len() / d;

            // PCA on centroids
            let pca_hp = if num_centroids > self.num_bits {
                let (hp, _) = self.compute_pca_flat(&centroids, num_centroids, d, self.num_bits);
                hp
            } else {
                random_hp
            };

            // Hash with PCA hyperplanes
            let hashes = self.hash_embeddings_flat(data, n, d, &pca_hp);
            all_hashes.push(hashes);
        }

        // Compute stability for each item
        self.stability_scores = (0..n)
            .into_par_iter()
            .map(|i| {
                // Count unique buckets for this item
                let mut buckets: Vec<u64> = all_hashes.iter().map(|h| h[i]).collect();
                buckets.sort();
                buckets.dedup();
                let unique_count = buckets.len();

                // stability = 1 - (unique - 1) / (num_seeds - 1)
                // 1 unique -> 1.0, num_seeds unique -> 0.0
                if self.num_stability_seeds == 1 {
                    1.0
                } else {
                    1.0 - (unique_count as f32 - 1.0) / (self.num_stability_seeds as f32 - 1.0)
                }
            })
            .collect();
    }

    /// Generate random hyperplanes
    fn generate_random_hyperplanes(&self, rng: &mut ChaCha8Rng, num_bits: usize) -> DMatrix<f32> {
        let mut data = Vec::with_capacity(num_bits * self.embedding_dim);
        for _ in 0..(num_bits * self.embedding_dim) {
            data.push(rng.gen_range(-1.0f32..1.0f32));
        }

        let mut hp = DMatrix::from_vec(num_bits, self.embedding_dim, data);

        // Normalize each row
        for i in 0..num_bits {
            let row = hp.row(i);
            let norm: f32 = row.iter().map(|x| x * x).sum::<f32>().sqrt();
            if norm > 0.0 {
                for j in 0..self.embedding_dim {
                    hp[(i, j)] /= norm;
                }
            }
        }

        hp
    }

    /// Hash embeddings from flat slice - uses ndarray with BLAS for fast matmul
    fn hash_embeddings_flat(&self, data: &[f32], n: usize, d: usize, hyperplanes: &DMatrix<f32>) -> Vec<u64> {
        let num_bits = hyperplanes.nrows();

        // Create ndarray view over flat data (zero-copy)
        let emb_view = ArrayView2::from_shape((n, d), data).unwrap();

        // Convert hyperplanes to ndarray and transpose: (bits x d) -> (d x bits)
        let mut hp_transposed = Array2::<f32>::zeros((d, num_bits));
        for i in 0..num_bits {
            for j in 0..d {
                hp_transposed[[j, i]] = hyperplanes[(i, j)];
            }
        }

        // BLAS-accelerated matrix multiply: (n x d) @ (d x bits) = (n x bits)
        let dots = emb_view.dot(&hp_transposed);

        // Convert dot products to hash values (parallel)
        (0..n)
            .into_par_iter()
            .map(|i| {
                let mut hash = 0u64;
                for bit_idx in 0..num_bits {
                    if dots[[i, bit_idx]] > 0.0 {
                        hash |= 1 << bit_idx;
                    }
                }
                hash
            })
            .collect()
    }

    /// Compute all centroids from flat data
    fn compute_all_centroids_flat(&self, data: &[f32], _n: usize, d: usize, hashes: &[u64], min_size: usize) -> Vec<f32> {
        let mut bucket_sizes: HashMap<u64, usize> = HashMap::new();
        for &hash in hashes {
            *bucket_sizes.entry(hash).or_default() += 1;
        }

        let valid_buckets: Vec<u64> = bucket_sizes
            .iter()
            .filter(|(_, &size)| size >= min_size)
            .map(|(&hash, _)| hash)
            .collect();

        let bucket_to_idx: HashMap<u64, usize> = valid_buckets
            .iter()
            .enumerate()
            .map(|(idx, &hash)| (hash, idx))
            .collect();

        let num_centroids = valid_buckets.len();
        if num_centroids == 0 {
            return Vec::new();
        }

        let mut sums = vec![0.0f32; num_centroids * d];
        let mut counts = vec![0usize; num_centroids];

        for (i, &hash) in hashes.iter().enumerate() {
            if let Some(&centroid_idx) = bucket_to_idx.get(&hash) {
                let row_start = i * d;
                let sum_start = centroid_idx * d;
                for j in 0..d {
                    sums[sum_start + j] += data[row_start + j];
                }
                counts[centroid_idx] += 1;
            }
        }

        // Normalize centroids
        sums.par_chunks_mut(d)
            .zip(counts.par_iter())
            .for_each(|(sum_chunk, &count)| {
                if count > 0 {
                    let n_f = count as f32;
                    for val in sum_chunk.iter_mut() {
                        *val /= n_f;
                    }
                    let norm: f32 = sum_chunk.iter().map(|x| x * x).sum::<f32>().sqrt();
                    if norm > 0.0 {
                        for val in sum_chunk.iter_mut() {
                            *val /= norm;
                        }
                    }
                }
            });

        sums.chunks(d)
            .zip(counts.iter())
            .filter(|(_, &count)| count > 0)
            .flat_map(|(chunk, _)| chunk.iter().copied())
            .collect()
    }

    /// Compute centroid from flat data for specific indices
    fn compute_centroid_flat(&self, data: &[f32], d: usize, indices: &[usize]) -> Vec<f32> {
        if indices.is_empty() {
            return vec![0.0f32; d];
        }

        let mut centroid = vec![0.0f32; d];
        for &idx in indices {
            let row_start = idx * d;
            for j in 0..d {
                centroid[j] += data[row_start + j];
            }
        }

        let n = indices.len() as f32;
        for val in &mut centroid {
            *val /= n;
        }

        let norm: f32 = centroid.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 0.0 {
            for val in &mut centroid {
                *val /= norm;
            }
        }
        centroid
    }

    /// Compute PCA hyperplanes from flat data
    fn compute_pca_flat(&self, data: &[f32], n: usize, d: usize, num_components: usize) -> (DMatrix<f32>, f32) {
        if n < 2 || d == 0 {
            return (
                self.generate_random_hyperplanes(&mut ChaCha8Rng::seed_from_u64(self.seed), num_components),
                0.0,
            );
        }

        let data_view = ArrayView2::from_shape((n, d), data).unwrap();
        let mean = data_view.mean_axis(ndarray::Axis(0)).unwrap();
        let centered = &data_view - &mean;
        let xtx = centered.t().dot(&centered);

        let k = num_components.min(d).min(n - 1);
        let (components, eigenvalues) = self.power_iteration_pca_ndarray(&xtx, k, d, 20);

        let total_variance = if !eigenvalues.is_empty() {
            let sum: f32 = eigenvalues.iter().sum();
            if sum > 0.0 {
                eigenvalues.iter().sum::<f32>() / (sum + 0.001)
            } else {
                0.0
            }
        } else {
            0.0
        };

        (components, total_variance.min(1.0))
    }

    /// Power iteration PCA using ndarray
    fn power_iteration_pca_ndarray(
        &self,
        xtx: &Array2<f32>,
        k: usize,
        d: usize,
        max_iter: usize,
    ) -> (DMatrix<f32>, Vec<f32>) {
        use ndarray::Array1;

        let mut components = DMatrix::<f32>::zeros(k, d);
        let mut eigenvalues = Vec::with_capacity(k);
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed + 999);
        let mut prev_components: Vec<Array1<f32>> = Vec::with_capacity(k);

        for comp_idx in 0..k {
            let v_data: Vec<f32> = (0..d).map(|_| rng.gen_range(-1.0f32..1.0f32)).collect();
            let mut v = Array1::from_vec(v_data);
            let norm = v.dot(&v).sqrt();
            v /= norm;

            for _ in 0..max_iter {
                let mut xtxv = xtx.dot(&v);

                for prev_vec in &prev_components {
                    let dot = xtxv.dot(prev_vec);
                    xtxv = &xtxv - &(dot * prev_vec);
                }

                let norm = xtxv.dot(&xtxv).sqrt();
                if norm > 1e-10 {
                    v = &xtxv / norm;
                }
            }

            for j in 0..d {
                components[(comp_idx, j)] = v[j];
            }

            prev_components.push(v.clone());

            let xtxv = xtx.dot(&v);
            let eigenvalue = v.dot(&xtxv);
            eigenvalues.push(eigenvalue);
        }

        (components, eigenvalues)
    }

    /// Cosine similarity between two vectors
    fn cosine_similarity(&self, a: &[f32], b: &[f32]) -> f32 {
        a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
    }

    // =========================================================================
    // Public Accessors
    // =========================================================================

    /// Get bucket IDs for all items
    pub fn get_bucket_ids(&self) -> &[u64] {
        &self.bucket_ids
    }

    /// Get bucket ID for a single item
    pub fn get_bucket_id(&self, idx: usize) -> Option<u64> {
        self.bucket_ids.get(idx).copied()
    }

    /// Get bucket sizes for all items
    pub fn get_bucket_sizes(&self) -> &[u32] {
        &self.bucket_sizes
    }

    /// Get centroid similarities for all items
    pub fn get_centroid_similarities(&self) -> &[f32] {
        &self.centroid_similarities
    }

    /// Get isolation scores for all items
    pub fn get_isolation_scores(&self) -> &[f32] {
        &self.isolation_scores
    }

    /// Get stability scores for all items (0-1, higher = more stable)
    pub fn get_stability_scores(&self) -> &[f32] {
        &self.stability_scores
    }

    /// Get classification report
    pub fn report(&self) -> DensityReport {
        let mean_bucket = if self.bucket_sizes.is_empty() {
            0.0
        } else {
            self.bucket_sizes.iter().map(|&x| x as f32).sum::<f32>() / self.bucket_sizes.len() as f32
        };

        let mut sorted_sizes: Vec<u32> = self.bucket_sizes.clone();
        sorted_sizes.sort();
        let median_bucket = if sorted_sizes.is_empty() {
            0
        } else {
            sorted_sizes[sorted_sizes.len() / 2] as usize
        };
        let max_bucket = sorted_sizes.last().copied().unwrap_or(0) as usize;

        let mean_centroid_sim = if self.centroid_similarities.is_empty() {
            0.0
        } else {
            self.centroid_similarities.iter().sum::<f32>() / self.centroid_similarities.len() as f32
        };

        let mean_isolation = if self.isolation_scores.is_empty() {
            0.0
        } else {
            self.isolation_scores.iter().sum::<f32>() / self.isolation_scores.len() as f32
        };

        let mean_stability = if self.stability_scores.is_empty() {
            0.0
        } else {
            self.stability_scores.iter().sum::<f32>() / self.stability_scores.len() as f32
        };

        DensityReport {
            corpus_size: self.bucket_ids.len(),
            num_buckets: self.num_buckets,
            stage1_variance_explained: self.stage1_variance,
            mean_bucket_size: mean_bucket,
            median_bucket_size: median_bucket,
            max_bucket_size: max_bucket,
            mean_centroid_similarity: mean_centroid_sim,
            mean_isolation_score: mean_isolation,
            mean_stability_score: mean_stability,
        }
    }

    /// Get PCA hyperplanes
    pub fn get_hyperplanes(&self) -> Option<&DMatrix<f32>> {
        self.hyperplanes.as_ref()
    }

    /// Check if fitted
    pub fn is_fitted(&self) -> bool {
        self.fitted
    }

    /// Get embedding dimension
    pub fn embedding_dim(&self) -> usize {
        self.embedding_dim
    }

    /// Adaptive Voronoi refinement: search radius based on item confidence
    ///
    /// Low-confidence items (low centroid_similarity) get wider search.
    /// High-confidence items get narrow search or skip entirely.
    ///
    /// Returns the number of items reassigned.
    pub fn voronoi_refine_adaptive_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
    ) -> usize {
        if !self.fitted || n == 0 {
            return 0;
        }

        // Determine Hamming radius per item based on centroid similarity
        // sim < 0.5 → 3, sim 0.5-0.7 → 2, sim > 0.7 → 1
        let item_hamming: Vec<u32> = self.centroid_similarities
            .iter()
            .map(|&sim| {
                if sim < 0.5 { 3 }
                else if sim < 0.7 { 2 }
                else { 1 }
            })
            .collect();

        // Get unique buckets
        let unique_buckets: Vec<u64> = {
            let mut buckets: Vec<u64> = self.bucket_ids.clone();
            buckets.sort();
            buckets.dedup();
            buckets
        };
        let num_buckets = unique_buckets.len();
        if num_buckets <= 1 {
            return 0;
        }

        let bucket_to_idx: HashMap<u64, usize> = unique_buckets
            .iter()
            .enumerate()
            .map(|(i, &b)| (b, i))
            .collect();

        // Build bucket -> item indices
        let mut bucket_item_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            bucket_item_indices.entry(bid).or_default().push(i);
        }

        // Compute centroids
        let mut centroids = Array2::<f32>::zeros((num_buckets, d));
        for (bucket_idx, &bucket_id) in unique_buckets.iter().enumerate() {
            if let Some(indices) = bucket_item_indices.get(&bucket_id) {
                let centroid = self.compute_centroid_flat(data, d, indices);
                for (j, &val) in centroid.iter().enumerate() {
                    centroids[[bucket_idx, j]] = val;
                }
            }
        }

        // Precompute neighbor sets for each Hamming distance
        let neighbors_by_hamming: Vec<Vec<Vec<usize>>> = (0..=3)
            .map(|max_h| {
                unique_buckets
                    .iter()
                    .map(|&bid| {
                        unique_buckets
                            .iter()
                            .enumerate()
                            .filter_map(|(idx, &other)| {
                                if (bid ^ other).count_ones() <= max_h {
                                    Some(idx)
                                } else {
                                    None
                                }
                            })
                            .collect()
                    })
                    .collect()
            })
            .collect();

        // Process items grouped by (bucket, hamming_radius) for batched BLAS
        use std::sync::atomic::{AtomicU64, Ordering};
        let new_ids: Vec<AtomicU64> = (0..n).map(|_| AtomicU64::new(0)).collect();

        // Group items by bucket and max hamming radius
        let mut bucket_hamming_groups: HashMap<(u64, u32), Vec<usize>> = HashMap::new();
        for (i, (&bid, &h)) in self.bucket_ids.iter().zip(item_hamming.iter()).enumerate() {
            bucket_hamming_groups.entry((bid, h)).or_default().push(i);
        }

        // Process groups in parallel
        let groups: Vec<_> = bucket_hamming_groups.into_iter().collect();
        groups.par_iter().for_each(|((bucket_id, hamming_radius), item_indices)| {
            let bucket_idx = bucket_to_idx[bucket_id];
            let neighbors = &neighbors_by_hamming[*hamming_radius as usize][bucket_idx];
            let num_neighbors = neighbors.len();

            // Build neighbor centroid matrix
            let mut neighbor_centroids = Array2::<f32>::zeros((num_neighbors, d));
            for (local_idx, &global_idx) in neighbors.iter().enumerate() {
                for j in 0..d {
                    neighbor_centroids[[local_idx, j]] = centroids[[global_idx, j]];
                }
            }

            // Build item matrix
            let num_items = item_indices.len();
            let mut item_matrix = Array2::<f32>::zeros((num_items, d));
            for (local_i, &global_i) in item_indices.iter().enumerate() {
                for j in 0..d {
                    item_matrix[[local_i, j]] = data[global_i * d + j];
                }
            }

            // BLAS matmul
            let sims = item_matrix.dot(&neighbor_centroids.t());

            // Argmax
            for (local_i, &global_i) in item_indices.iter().enumerate() {
                let row = sims.row(local_i);
                let best_local = row.iter()
                    .enumerate()
                    .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                    .map(|(idx, _)| idx)
                    .unwrap_or(0);
                new_ids[global_i].store(unique_buckets[neighbors[best_local]], Ordering::Relaxed);
            }
        });

        let new_bucket_ids: Vec<u64> = new_ids.into_iter().map(|a| a.into_inner()).collect();

        // Count reassignments and update
        let reassigned = self.bucket_ids
            .iter()
            .zip(new_bucket_ids.iter())
            .filter(|(old, new)| old != new)
            .count();

        self.bucket_ids = new_bucket_ids;

        // Recompute metrics
        let mut new_bucket_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            new_bucket_indices.entry(bid).or_default().push(i);
        }
        self.num_buckets = new_bucket_indices.len();

        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &new_bucket_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(data, d, indices);
            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &data[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        reassigned
    }

    /// Hierarchical LSH: coarse global hash + fine region-specific hash
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
    /// * `data` - Flat embedding data (n * d elements)
    /// * `n` - Number of samples
    /// * `d` - Embedding dimension
    /// * `coarse_bits` - Bits for global hash (default: 6)
    /// * `fine_bits` - Bits for per-region hash (default: 4)
    ///
    /// # Returns
    /// Self for chaining
    pub fn fit_hierarchical_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
        coarse_bits: usize,
        fine_bits: usize,
    ) -> &Self {
        if n == 0 || d != self.embedding_dim {
            self.fitted = true;
            return self;
        }

        // Normalize data into a flat buffer
        let mut normalized = vec![0.0f32; n * d];
        normalized
            .par_chunks_mut(d)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * d;
                let in_row = &data[start..start + d];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        // =========================================================================
        // Stage 1: Coarse hash with global PCA on RAW DATA (not centroids)
        // =========================================================================

        // PCA directly on embeddings - captures global variance directions
        let (coarse_hp, variance) = self.compute_pca_flat(&normalized, n, d, coarse_bits);
        self.stage1_variance = variance;

        // Hash all items with coarse hyperplanes
        let coarse_hashes = self.hash_embeddings_flat(&normalized, n, d, &coarse_hp);

        // Build coarse bucket -> item indices mapping
        let mut coarse_bucket_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &hash) in coarse_hashes.iter().enumerate() {
            coarse_bucket_indices.entry(hash).or_default().push(i);
        }

        // =========================================================================
        // Stage 2: Fine hash with per-region PCA on RAW DATA
        // =========================================================================

        // For each coarse bucket, compute region-specific PCA and fine hash
        let mut final_bucket_ids = vec![0u64; n];

        // Process coarse buckets in parallel
        let coarse_buckets: Vec<(u64, Vec<usize>)> = coarse_bucket_indices.into_iter().collect();

        let fine_results: Vec<(Vec<usize>, Vec<u64>)> = coarse_buckets
            .par_iter()
            .map(|(coarse_id, indices)| {
                let num_items = indices.len();

                // Extract region items
                let mut region_data = vec![0.0f32; num_items * d];
                for (local_i, &global_i) in indices.iter().enumerate() {
                    region_data[local_i * d..(local_i + 1) * d]
                        .copy_from_slice(&normalized[global_i * d..(global_i + 1) * d]);
                }

                // Compute fine hyperplanes for this region - PCA directly on data
                let fine_hp = if num_items > fine_bits + 1 {
                    let (hp, _) = self.compute_pca_flat(&region_data, num_items, d, fine_bits);
                    hp
                } else {
                    // Not enough items - use random hyperplanes
                    let mut rng = ChaCha8Rng::seed_from_u64(self.seed + *coarse_id);
                    self.generate_random_hyperplanes(&mut rng, fine_bits)
                };

                // Hash region items with fine hyperplanes
                let fine_hashes = self.hash_embeddings_flat(&region_data, num_items, d, &fine_hp);

                // Combine coarse and fine into final bucket IDs
                let combined: Vec<u64> = fine_hashes
                    .iter()
                    .map(|&fine_id| (*coarse_id << fine_bits) | fine_id)
                    .collect();

                (indices.clone(), combined)
            })
            .collect();

        // Scatter results back to original indices
        for (indices, combined_ids) in fine_results {
            for (local_i, &global_i) in indices.iter().enumerate() {
                final_bucket_ids[global_i] = combined_ids[local_i];
            }
        }

        // Store hyperplanes (coarse only for now - fine are region-specific)
        self.hyperplanes = Some(coarse_hp);
        self.bucket_ids = final_bucket_ids;
        self.num_bits = coarse_bits + fine_bits; // Update total bits

        // Build bucket mapping and compute metrics
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in self.bucket_ids.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(&normalized, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &normalized[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Compute isolation and stability scores
        self.compute_isolation_scores_flat(&normalized, n, d, 10);
        self.compute_stability_scores_flat(&normalized, n, d);

        self.fitted = true;
        self
    }

    /// Voronoi refinement: reassign items to nearest centroid among Hamming neighbors
    ///
    /// This refines LSH bucket assignments by checking if a nearby bucket's centroid
    /// is actually closer. Only checks buckets within `max_hamming_distance` bits
    /// of the current bucket (cheap Voronoi).
    ///
    /// Uses BLAS-accelerated matrix multiply for similarity computation.
    ///
    /// Returns the number of items reassigned.
    pub fn voronoi_refine_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
        max_hamming_distance: u32,
    ) -> usize {
        if !self.fitted || n == 0 {
            return 0;
        }

        // Step 1: Get unique buckets and compute centroids
        let unique_buckets: Vec<u64> = {
            let mut buckets: Vec<u64> = self.bucket_ids.clone();
            buckets.sort();
            buckets.dedup();
            buckets
        };
        let num_buckets = unique_buckets.len();
        if num_buckets <= 1 {
            return 0;
        }

        let bucket_to_idx: HashMap<u64, usize> = unique_buckets
            .iter()
            .enumerate()
            .map(|(i, &b)| (b, i))
            .collect();

        // Build bucket -> item indices mapping
        let mut bucket_item_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            bucket_item_indices.entry(bid).or_default().push(i);
        }

        // Compute centroids for all buckets as ndarray (num_buckets x d)
        let mut centroids = Array2::<f32>::zeros((num_buckets, d));
        for (bucket_idx, &bucket_id) in unique_buckets.iter().enumerate() {
            if let Some(indices) = bucket_item_indices.get(&bucket_id) {
                let centroid = self.compute_centroid_flat(data, d, indices);
                for (j, &val) in centroid.iter().enumerate() {
                    centroids[[bucket_idx, j]] = val;
                }
            }
        }

        // Step 2: Choose algorithm based on restriction level
        let new_bucket_ids: Vec<u64> = if max_hamming_distance >= self.num_bits as u32 {
            // Full Voronoi: single BLAS call for all similarities
            let data_view = ArrayView2::from_shape((n, d), data).unwrap();
            let similarities = data_view.dot(&centroids.t());

            (0..n)
                .into_par_iter()
                .map(|i| {
                    let row = similarities.row(i);
                    let best_idx = row.iter()
                        .enumerate()
                        .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                        .map(|(idx, _)| idx)
                        .unwrap_or(0);
                    unique_buckets[best_idx]
                })
                .collect()
        } else {
            // Cheap Voronoi: per-bucket BLAS calls (less total FLOPS)
            // Generate Hamming neighbors by bit-flipping (O(buckets * C(bits,k)) vs O(buckets²))
            let neighbor_indices: Vec<Vec<usize>> = unique_buckets
                .par_iter()
                .map(|&bid| {
                    let mut neighbors = Vec::new();

                    // Generate all Hamming neighbors by flipping bits
                    // Hamming 0: self
                    if let Some(&idx) = bucket_to_idx.get(&bid) {
                        neighbors.push(idx);
                    }

                    // Hamming 1: flip single bits
                    if max_hamming_distance >= 1 {
                        for i in 0..self.num_bits {
                            let neighbor = bid ^ (1u64 << i);
                            if let Some(&idx) = bucket_to_idx.get(&neighbor) {
                                neighbors.push(idx);
                            }
                        }
                    }

                    // Hamming 2: flip pairs of bits
                    if max_hamming_distance >= 2 {
                        for i in 0..self.num_bits {
                            for j in (i + 1)..self.num_bits {
                                let neighbor = bid ^ (1u64 << i) ^ (1u64 << j);
                                if let Some(&idx) = bucket_to_idx.get(&neighbor) {
                                    neighbors.push(idx);
                                }
                            }
                        }
                    }

                    // Hamming 3: flip triplets of bits
                    if max_hamming_distance >= 3 {
                        for i in 0..self.num_bits {
                            for j in (i + 1)..self.num_bits {
                                for k in (j + 1)..self.num_bits {
                                    let neighbor = bid ^ (1u64 << i) ^ (1u64 << j) ^ (1u64 << k);
                                    if let Some(&idx) = bucket_to_idx.get(&neighbor) {
                                        neighbors.push(idx);
                                    }
                                }
                            }
                        }
                    }

                    neighbors
                })
                .collect();

            // Process buckets in parallel, each with its own small BLAS call
            use std::sync::atomic::{AtomicU64, Ordering};
            let new_ids: Vec<AtomicU64> = (0..n).map(|_| AtomicU64::new(0)).collect();

            unique_buckets.par_iter().enumerate().for_each(|(bucket_idx, &bucket_id)| {
                let item_indices = match bucket_item_indices.get(&bucket_id) {
                    Some(indices) => indices,
                    None => return,
                };

                let neighbors = &neighbor_indices[bucket_idx];
                let num_neighbors = neighbors.len();

                // Build neighbor centroid matrix (num_neighbors x d)
                let mut neighbor_centroids = Array2::<f32>::zeros((num_neighbors, d));
                for (local_idx, &global_idx) in neighbors.iter().enumerate() {
                    for j in 0..d {
                        neighbor_centroids[[local_idx, j]] = centroids[[global_idx, j]];
                    }
                }

                // Build item matrix for this bucket (num_items x d)
                let num_items = item_indices.len();
                let mut item_matrix = Array2::<f32>::zeros((num_items, d));
                for (local_i, &global_i) in item_indices.iter().enumerate() {
                    for j in 0..d {
                        item_matrix[[local_i, j]] = data[global_i * d + j];
                    }
                }

                // Small BLAS call: (num_items x d) @ (d x num_neighbors)
                let sims = item_matrix.dot(&neighbor_centroids.t());

                // Argmax for each item
                for (local_i, &global_i) in item_indices.iter().enumerate() {
                    let row = sims.row(local_i);
                    let best_local = row.iter()
                        .enumerate()
                        .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                        .map(|(idx, _)| idx)
                        .unwrap_or(0);
                    new_ids[global_i].store(unique_buckets[neighbors[best_local]], Ordering::Relaxed);
                }
            });

            new_ids.into_iter().map(|a| a.into_inner()).collect()
        };

        // Step 3: Count reassignments and update
        let reassigned = self.bucket_ids
            .iter()
            .zip(new_bucket_ids.iter())
            .filter(|(old, new)| old != new)
            .count();

        self.bucket_ids = new_bucket_ids;

        // Recompute bucket sizes and centroid similarities
        let mut new_bucket_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            new_bucket_indices.entry(bid).or_default().push(i);
        }
        self.num_buckets = new_bucket_indices.len();

        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &new_bucket_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(data, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &data[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        reassigned
    }

    /// Recursive density-based splitting: subdivide dense buckets
    ///
    /// Algorithm:
    /// 1. LSH/PCA on data → buckets
    /// 2. For each bucket:
    ///    - If dense (size > threshold): recurse on bucket contents
    ///    - If sparse (size <= threshold): done, this is a leaf
    ///
    /// Dense regions get more splits, sparse regions stop early.
    /// Adaptive resolution based on local density.
    ///
    /// # Arguments
    /// * `data` - Flat embedding data
    /// * `n` - Number of samples
    /// * `d` - Embedding dimension
    /// * `bits_per_level` - Bits to use at each recursion level (default: 4)
    /// * `max_depth` - Maximum recursion depth (default: 4)
    /// * `min_bucket_size` - Stop splitting below this size (default: 20)
    ///
    /// # Returns
    /// Self for chaining
    pub fn fit_recursive_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
        bits_per_level: usize,
        max_depth: usize,
        min_bucket_size: usize,
    ) -> &Self {
        if n == 0 || d != self.embedding_dim {
            self.fitted = true;
            return self;
        }

        // Normalize data
        let mut normalized = vec![0.0f32; n * d];
        normalized
            .par_chunks_mut(d)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * d;
                let in_row = &data[start..start + d];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        // Initialize bucket IDs to 0
        let mut bucket_ids = vec![0u64; n];
        let mut current_bit_offset = 0usize;

        // Track which items are still "active" (in buckets that need splitting)
        // Initially all items are active with bucket prefix 0
        let mut active_groups: Vec<(u64, Vec<usize>)> = vec![(0u64, (0..n).collect())];

        for depth in 0..max_depth {
            if active_groups.is_empty() {
                break;
            }

            let mut next_active_groups: Vec<(u64, Vec<usize>)> = Vec::new();

            // Process each active group
            for (prefix, indices) in active_groups {
                let group_size = indices.len();

                // If small enough, this group is done (leaf)
                if group_size <= min_bucket_size {
                    // Keep current bucket ID (prefix is already set)
                    continue;
                }

                // Extract data for this group
                let mut group_data = vec![0.0f32; group_size * d];
                for (local_i, &global_i) in indices.iter().enumerate() {
                    group_data[local_i * d..(local_i + 1) * d]
                        .copy_from_slice(&normalized[global_i * d..(global_i + 1) * d]);
                }

                // LSH/PCA on this group
                let group_hyperplanes = self.compute_group_hyperplanes(
                    &group_data, group_size, d, bits_per_level
                );

                // Hash group items
                let group_hashes = self.hash_embeddings_flat(
                    &group_data, group_size, d, &group_hyperplanes
                );

                // Update bucket IDs with new bits
                for (local_i, &global_i) in indices.iter().enumerate() {
                    let new_bits = group_hashes[local_i];
                    bucket_ids[global_i] = prefix | (new_bits << current_bit_offset);
                }

                // Group items by their new hash within this group
                let mut sub_buckets: HashMap<u64, Vec<usize>> = HashMap::new();
                for (local_i, &global_i) in indices.iter().enumerate() {
                    let full_id = bucket_ids[global_i];
                    sub_buckets.entry(full_id).or_default().push(global_i);
                }

                // Add dense sub-buckets to next iteration
                for (full_id, sub_indices) in sub_buckets {
                    if sub_indices.len() > min_bucket_size {
                        next_active_groups.push((full_id, sub_indices));
                    }
                    // Sparse buckets are done - their IDs are already set
                }
            }

            active_groups = next_active_groups;
            current_bit_offset += bits_per_level;
        }

        // Store results
        self.bucket_ids = bucket_ids;
        self.num_bits = current_bit_offset; // Total bits used

        // Build bucket mapping and compute metrics
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in self.bucket_ids.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(&normalized, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &normalized[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Compute isolation and stability scores
        self.compute_isolation_scores_flat(&normalized, n, d, 10);
        // Skip stability for recursive (different hyperplanes per group)
        self.stability_scores = vec![1.0f32; n];

        self.fitted = true;
        self
    }

    /// Compute hyperplanes for a group using LSH → centroids → PCA
    fn compute_group_hyperplanes(
        &self,
        data: &[f32],
        n: usize,
        d: usize,
        num_bits: usize,
    ) -> DMatrix<f32> {
        if n <= num_bits + 1 {
            // Not enough data for PCA, use random
            let mut rng = ChaCha8Rng::seed_from_u64(self.seed + n as u64);
            return self.generate_random_hyperplanes(&mut rng, num_bits);
        }

        // Random hash to get initial buckets
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed + n as u64);
        let random_hp = self.generate_random_hyperplanes(&mut rng, num_bits);
        let random_hashes = self.hash_embeddings_flat(data, n, d, &random_hp);

        // Compute centroids
        let centroids = self.compute_all_centroids_flat(data, n, d, &random_hashes, 1);
        let num_centroids = centroids.len() / d;

        if num_centroids > num_bits {
            let (pca_hp, _) = self.compute_pca_flat(&centroids, num_centroids, d, num_bits);
            pca_hp
        } else {
            random_hp
        }
    }

    /// ITQ (Iterative Quantization): learn rotation to minimize quantization error
    ///
    /// Standard PCA-LSH uses sign(X @ PCA.T) which loses information near zero.
    /// ITQ finds a rotation R such that sign(X @ PCA.T @ R) has minimal quantization loss.
    ///
    /// Algorithm:
    /// 1. Compute PCA projections V = X @ PCA.T
    /// 2. Iterate: B = sign(V @ R), then solve Procrustes for R
    /// 3. Final hyperplanes = PCA @ R
    ///
    /// Typically gives 5-15% improvement over raw PCA.
    ///
    /// # Arguments
    /// * `data` - Flat embedding data
    /// * `n` - Number of samples
    /// * `d` - Embedding dimension
    /// * `max_iterations` - ITQ iterations (default: 50)
    ///
    /// # Returns
    /// Self for chaining
    pub fn fit_itq_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
        max_iterations: usize,
    ) -> &Self {
        if n == 0 || d != self.embedding_dim {
            self.fitted = true;
            return self;
        }

        // Normalize data
        let mut normalized = vec![0.0f32; n * d];
        normalized
            .par_chunks_mut(d)
            .enumerate()
            .for_each(|(i, out_row)| {
                let start = i * d;
                let in_row = &data[start..start + d];
                let norm: f32 = in_row.iter().map(|x| x * x).sum::<f32>().sqrt();
                if norm > 0.0 {
                    for (j, &val) in in_row.iter().enumerate() {
                        out_row[j] = val / norm;
                    }
                } else {
                    out_row.copy_from_slice(in_row);
                }
            });

        // Step 1: Standard PCA to get initial hyperplanes
        let mut rng = ChaCha8Rng::seed_from_u64(self.seed);
        let random_hp = self.generate_random_hyperplanes(&mut rng, self.num_bits);
        let random_hashes = self.hash_embeddings_flat(&normalized, n, d, &random_hp);

        let centroids = self.compute_all_centroids_flat(&normalized, n, d, &random_hashes, 2);
        let num_centroids = centroids.len() / d;

        let (pca_hp, variance) = if num_centroids > self.num_bits {
            self.compute_pca_flat(&centroids, num_centroids, d, self.num_bits)
        } else {
            (random_hp.clone(), 0.0)
        };
        self.stage1_variance = variance;

        let k = self.num_bits;

        // Step 2: Compute PCA projections V = X @ PCA.T (n × k)
        // PCA is k × d, so we need X @ PCA.T = (n × d) @ (d × k)
        let data_view = ArrayView2::from_shape((n, d), &normalized).unwrap();
        let mut pca_t = Array2::<f32>::zeros((d, k));
        for i in 0..k {
            for j in 0..d {
                pca_t[[j, i]] = pca_hp[(i, j)];
            }
        }
        let v = data_view.dot(&pca_t); // n × k

        // Step 3: Initialize rotation R = Identity (k × k)
        let mut r = DMatrix::<f32>::identity(k, k);

        // Step 4: ITQ iterations
        for _iter in 0..max_iterations {
            // Compute V @ R (n × k)
            let mut vr = Array2::<f32>::zeros((n, k));
            for i in 0..n {
                for j in 0..k {
                    let mut sum = 0.0f32;
                    for l in 0..k {
                        sum += v[[i, l]] * r[(l, j)];
                    }
                    vr[[i, j]] = sum;
                }
            }

            // B = sign(V @ R)
            let b: Array2<f32> = vr.mapv(|x| if x >= 0.0 { 1.0 } else { -1.0 });

            // Solve Procrustes: minimize ||V @ R - B||² subject to R orthogonal
            // C = V.T @ B (k × k)
            let mut c = DMatrix::<f32>::zeros(k, k);
            for i in 0..k {
                for j in 0..k {
                    let mut sum = 0.0f32;
                    for l in 0..n {
                        sum += v[[l, i]] * b[[l, j]];
                    }
                    c[(i, j)] = sum;
                }
            }

            // SVD of C: C = U @ S @ V.T
            // R_new = U @ V.T (closest orthogonal matrix to C)
            let svd = c.svd(true, true);
            if let (Some(u), Some(vt)) = (svd.u, svd.v_t) {
                // R = U @ V.T
                r = &u * &vt;
            }
        }

        // Step 5: Final hyperplanes = PCA @ R
        // PCA is k × d, R is k × k
        // rotated_hp[i] = sum_j R[j,i] * PCA[j]
        let mut rotated_hp = DMatrix::<f32>::zeros(k, d);
        for i in 0..k {
            for j in 0..d {
                let mut sum = 0.0f32;
                for l in 0..k {
                    sum += r[(l, i)] * pca_hp[(l, j)];
                }
                rotated_hp[(i, j)] = sum;
            }
        }

        // Normalize rows of rotated hyperplanes
        for i in 0..k {
            let norm: f32 = (0..d).map(|j| rotated_hp[(i, j)].powi(2)).sum::<f32>().sqrt();
            if norm > 0.0 {
                for j in 0..d {
                    rotated_hp[(i, j)] /= norm;
                }
            }
        }

        self.hyperplanes = Some(rotated_hp.clone());

        // Step 6: Hash with rotated hyperplanes
        let hashes = self.hash_embeddings_flat(&normalized, n, d, &rotated_hp);
        self.bucket_ids = hashes.clone();

        // Build bucket mapping
        let mut bucket_to_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (idx, &hash) in hashes.iter().enumerate() {
            bucket_to_indices.entry(hash).or_default().push(idx);
        }
        self.num_buckets = bucket_to_indices.len();

        // Compute per-item metrics
        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &bucket_to_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(&normalized, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &normalized[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        // Compute isolation and stability scores
        self.compute_isolation_scores_flat(&normalized, n, d, 10);
        self.compute_stability_scores_flat(&normalized, n, d);

        self.fitted = true;
        self
    }

    /// Margin-based selective refinement: only refine low-confidence items
    ///
    /// Items near hyperplane boundaries (low margin) are candidates for misassignment.
    /// This method only refines those items, skipping high-confidence ones.
    ///
    /// Margin = minimum |dot product| across all hyperplanes.
    /// Low margin = item is close to at least one decision boundary.
    ///
    /// # Arguments
    /// * `data` - Flat embedding data (same as fit)
    /// * `n` - Number of samples
    /// * `d` - Embedding dimension
    /// * `margin_threshold` - Items with margin below this are refined (default: 0.1)
    /// * `max_hamming_distance` - Hamming radius for neighbor search (default: 2)
    ///
    /// # Returns
    /// (items_refined, items_reassigned) - how many were checked vs actually moved
    pub fn voronoi_refine_margin_flat(
        &mut self,
        data: &[f32],
        n: usize,
        d: usize,
        margin_threshold: f32,
        max_hamming_distance: u32,
    ) -> (usize, usize) {
        if !self.fitted || n == 0 {
            return (0, 0);
        }

        let hyperplanes = match &self.hyperplanes {
            Some(hp) => hp,
            None => return (0, 0),
        };

        // Step 1: Compute margins for all items
        // Margin = min(|dot product with hyperplane|) across all hyperplanes
        let num_hp = hyperplanes.nrows();

        // Convert hyperplanes to ndarray for BLAS
        let mut hp_array = Array2::<f32>::zeros((num_hp, d));
        for i in 0..num_hp {
            for j in 0..d {
                hp_array[[i, j]] = hyperplanes[(i, j)];
            }
        }

        // Compute all dot products: (n x d) @ (d x num_hp) = (n x num_hp)
        let data_view = ArrayView2::from_shape((n, d), data).unwrap();
        let dots = data_view.dot(&hp_array.t());

        // Compute margin for each item (min absolute dot product)
        let margins: Vec<f32> = (0..n)
            .into_par_iter()
            .map(|i| {
                let row = dots.row(i);
                row.iter()
                    .map(|&x| x.abs())
                    .min_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                    .unwrap_or(0.0)
            })
            .collect();

        // Step 2: Identify low-margin items to refine
        let low_margin_indices: Vec<usize> = margins
            .iter()
            .enumerate()
            .filter(|(_, &m)| m < margin_threshold)
            .map(|(i, _)| i)
            .collect();

        let items_to_refine = low_margin_indices.len();
        if items_to_refine == 0 {
            return (0, 0);
        }

        // Step 3: Get unique buckets and compute centroids (same as voronoi_refine)
        let unique_buckets: Vec<u64> = {
            let mut buckets: Vec<u64> = self.bucket_ids.clone();
            buckets.sort();
            buckets.dedup();
            buckets
        };
        let num_buckets = unique_buckets.len();
        if num_buckets <= 1 {
            return (items_to_refine, 0);
        }

        let bucket_to_idx: HashMap<u64, usize> = unique_buckets
            .iter()
            .enumerate()
            .map(|(i, &b)| (b, i))
            .collect();

        // Build bucket -> item indices mapping
        let mut bucket_item_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            bucket_item_indices.entry(bid).or_default().push(i);
        }

        // Compute centroids
        let mut centroids = Array2::<f32>::zeros((num_buckets, d));
        for (bucket_idx, &bucket_id) in unique_buckets.iter().enumerate() {
            if let Some(indices) = bucket_item_indices.get(&bucket_id) {
                let centroid = self.compute_centroid_flat(data, d, indices);
                for (j, &val) in centroid.iter().enumerate() {
                    centroids[[bucket_idx, j]] = val;
                }
            }
        }

        // Step 4: Generate Hamming neighbors for each bucket (same bit-flip approach)
        let neighbor_indices: Vec<Vec<usize>> = unique_buckets
            .par_iter()
            .map(|&bid| {
                let mut neighbors = Vec::new();

                if let Some(&idx) = bucket_to_idx.get(&bid) {
                    neighbors.push(idx);
                }

                if max_hamming_distance >= 1 {
                    for i in 0..self.num_bits {
                        let neighbor = bid ^ (1u64 << i);
                        if let Some(&idx) = bucket_to_idx.get(&neighbor) {
                            neighbors.push(idx);
                        }
                    }
                }

                if max_hamming_distance >= 2 {
                    for i in 0..self.num_bits {
                        for j in (i + 1)..self.num_bits {
                            let neighbor = bid ^ (1u64 << i) ^ (1u64 << j);
                            if let Some(&idx) = bucket_to_idx.get(&neighbor) {
                                neighbors.push(idx);
                            }
                        }
                    }
                }

                neighbors
            })
            .collect();

        // Step 5: Refine only low-margin items
        use std::sync::atomic::{AtomicUsize, Ordering};
        let reassigned_count = AtomicUsize::new(0);

        let new_bucket_ids: Vec<u64> = (0..n)
            .into_par_iter()
            .map(|i| {
                // If high margin, keep original bucket
                if margins[i] >= margin_threshold {
                    return self.bucket_ids[i];
                }

                // Low margin - check neighbor centroids
                let current_bucket = self.bucket_ids[i];
                let bucket_idx = match bucket_to_idx.get(&current_bucket) {
                    Some(&idx) => idx,
                    None => return current_bucket,
                };

                let neighbors = &neighbor_indices[bucket_idx];
                let item_row = &data[i * d..(i + 1) * d];

                // Find best centroid among neighbors
                let mut best_bucket = current_bucket;
                let mut best_sim = f32::NEG_INFINITY;

                for &neighbor_idx in neighbors {
                    let mut sim = 0.0f32;
                    for j in 0..d {
                        sim += item_row[j] * centroids[[neighbor_idx, j]];
                    }
                    if sim > best_sim {
                        best_sim = sim;
                        best_bucket = unique_buckets[neighbor_idx];
                    }
                }

                if best_bucket != current_bucket {
                    reassigned_count.fetch_add(1, Ordering::Relaxed);
                }

                best_bucket
            })
            .collect();

        let items_reassigned = reassigned_count.load(Ordering::Relaxed);

        // Step 6: Update bucket assignments and metrics
        self.bucket_ids = new_bucket_ids;

        let mut new_bucket_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            new_bucket_indices.entry(bid).or_default().push(i);
        }
        self.num_buckets = new_bucket_indices.len();

        self.bucket_sizes = vec![0u32; n];
        self.centroid_similarities = vec![0.0f32; n];

        for (&_bucket_id, indices) in &new_bucket_indices {
            let bucket_size = indices.len() as u32;
            let centroid = self.compute_centroid_flat(data, d, indices);

            for &idx in indices {
                self.bucket_sizes[idx] = bucket_size;
                let row = &data[idx * d..(idx + 1) * d];
                self.centroid_similarities[idx] = self.cosine_similarity(row, &centroid);
            }
        }

        (items_to_refine, items_reassigned)
    }

    /// Analyze bridge items to discover region connectivity
    ///
    /// Bridges are items with low centroid similarity - they sit between regions.
    /// This analysis finds:
    /// 1. Which items are bridges
    /// 2. Which buckets each bridge connects
    /// 3. A region adjacency matrix showing how regions connect
    ///
    /// # Arguments
    /// * `data` - Flat embedding data (same as fit)
    /// * `n` - Number of samples
    /// * `d` - Embedding dimension
    /// * `bridge_threshold` - Items with centroid_sim below this are bridges (default: 0.5)
    /// * `connection_threshold` - Min similarity to consider a bridge connected to a bucket (default: 0.3)
    ///
    /// # Returns
    /// BridgeAnalysis struct with connectivity information
    pub fn analyze_bridges_flat(
        &self,
        data: &[f32],
        n: usize,
        d: usize,
        bridge_threshold: f32,
        connection_threshold: f32,
    ) -> BridgeAnalysis {
        if !self.fitted || n == 0 {
            return BridgeAnalysis {
                bridge_indices: Vec::new(),
                bridge_connections: Vec::new(),
                bucket_ids: Vec::new(),
                adjacency_matrix: Vec::new(),
                n_buckets: 0,
                bridge_threshold,
            };
        }

        // Get unique buckets and build centroids
        let unique_buckets: Vec<u64> = {
            let mut buckets: Vec<u64> = self.bucket_ids.clone();
            buckets.sort();
            buckets.dedup();
            buckets
        };
        let n_buckets = unique_buckets.len();

        let bucket_to_idx: HashMap<u64, usize> = unique_buckets
            .iter()
            .enumerate()
            .map(|(i, &b)| (b, i))
            .collect();

        // Build bucket -> item indices
        let mut bucket_item_indices: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, &bid) in self.bucket_ids.iter().enumerate() {
            bucket_item_indices.entry(bid).or_default().push(i);
        }

        // Compute centroids for all buckets
        let mut centroids = Array2::<f32>::zeros((n_buckets, d));
        for (bucket_idx, &bucket_id) in unique_buckets.iter().enumerate() {
            if let Some(indices) = bucket_item_indices.get(&bucket_id) {
                let centroid = self.compute_centroid_flat(data, d, indices);
                for (j, &val) in centroid.iter().enumerate() {
                    centroids[[bucket_idx, j]] = val;
                }
            }
        }

        // Find bridge items (low centroid similarity)
        let bridge_indices: Vec<usize> = self.centroid_similarities
            .iter()
            .enumerate()
            .filter(|(_, &sim)| sim < bridge_threshold)
            .map(|(i, _)| i)
            .collect();

        // For each bridge, find which buckets it's connected to
        let bridge_connections: Vec<(usize, u64, Vec<u64>)> = bridge_indices
            .par_iter()
            .map(|&item_idx| {
                let item_row = &data[item_idx * d..(item_idx + 1) * d];
                let primary_bucket = self.bucket_ids[item_idx];

                // Compute similarity to all bucket centroids
                let mut connected: Vec<u64> = Vec::new();
                for (bucket_idx, &bucket_id) in unique_buckets.iter().enumerate() {
                    if bucket_id == primary_bucket {
                        continue; // Skip own bucket
                    }
                    let mut sim = 0.0f32;
                    for j in 0..d {
                        sim += item_row[j] * centroids[[bucket_idx, j]];
                    }
                    if sim >= connection_threshold {
                        connected.push(bucket_id);
                    }
                }

                (item_idx, primary_bucket, connected)
            })
            .collect();

        // Build adjacency matrix
        let mut adjacency = vec![0u32; n_buckets * n_buckets];
        for (_, primary_bucket, connected) in &bridge_connections {
            let primary_idx = bucket_to_idx[primary_bucket];
            for &other_bucket in connected {
                let other_idx = bucket_to_idx[&other_bucket];
                // Symmetric: bridge connects both ways
                adjacency[primary_idx * n_buckets + other_idx] += 1;
                adjacency[other_idx * n_buckets + primary_idx] += 1;
            }
        }

        BridgeAnalysis {
            bridge_indices,
            bridge_connections,
            bucket_ids: unique_buckets,
            adjacency_matrix: adjacency,
            n_buckets,
            bridge_threshold,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn generate_test_embeddings(n: usize, dim: usize, seed: u64) -> Vec<Vec<f32>> {
        let mut rng = ChaCha8Rng::seed_from_u64(seed);
        (0..n)
            .map(|_| {
                let mut emb: Vec<f32> = (0..dim).map(|_| rng.gen_range(-1.0..1.0)).collect();
                let norm: f32 = emb.iter().map(|x| x * x).sum::<f32>().sqrt();
                for x in &mut emb {
                    *x /= norm;
                }
                emb
            })
            .collect()
    }

    #[test]
    fn test_classifier_creation() {
        let classifier = DensityClassifier::with_defaults(384);
        assert!(!classifier.is_fitted());
    }

    #[test]
    fn test_fit_small_corpus() {
        let embeddings = generate_test_embeddings(100, 128, 42);
        let mut classifier = DensityClassifier::with_defaults(128);
        classifier.fit(&embeddings);

        assert!(classifier.is_fitted());
        let report = classifier.report();
        assert_eq!(report.corpus_size, 100);
        assert!(report.mean_centroid_similarity > 0.0);
        assert!(report.mean_isolation_score > 0.0);
    }

    #[test]
    fn test_raw_scores() {
        let embeddings = generate_test_embeddings(100, 128, 42);
        let mut classifier = DensityClassifier::with_defaults(128);
        classifier.fit(&embeddings);

        assert_eq!(classifier.get_bucket_sizes().len(), 100);
        assert_eq!(classifier.get_centroid_similarities().len(), 100);
        assert_eq!(classifier.get_isolation_scores().len(), 100);
        assert_eq!(classifier.get_stability_scores().len(), 100);

        // All centroid similarities should be between -1 and 1 (cosine similarity range)
        for &sim in classifier.get_centroid_similarities() {
            assert!(sim >= -1.0 && sim <= 1.0 + 1e-6, "sim={} out of range", sim);
        }

        // Isolation scores should be positive (top_k - median)
        for &iso in classifier.get_isolation_scores() {
            assert!(iso >= 0.0);
        }

        // Stability scores should be between 0 and 1
        for &stab in classifier.get_stability_scores() {
            assert!(stab >= 0.0 && stab <= 1.0, "stability={} out of range", stab);
        }
    }

    #[test]
    fn test_stability_seeds() {
        let embeddings = generate_test_embeddings(50, 64, 42);

        // With 1 seed, all stability scores should be 1.0
        let mut clf1 = DensityClassifier::new(64, 10, 31, 1);
        clf1.fit(&embeddings);
        for &stab in clf1.get_stability_scores() {
            assert_eq!(stab, 1.0);
        }

        // With 5 seeds, stability scores should be in valid range [0, 1]
        let mut clf5 = DensityClassifier::new(64, 10, 31, 5);
        clf5.fit(&embeddings);
        for &stab in clf5.get_stability_scores() {
            assert!(stab >= 0.0 && stab <= 1.0, "stability={} out of range", stab);
        }

        // Report should include mean stability
        let report = clf5.report();
        assert!(report.mean_stability_score >= 0.0 && report.mean_stability_score <= 1.0);
    }
}
