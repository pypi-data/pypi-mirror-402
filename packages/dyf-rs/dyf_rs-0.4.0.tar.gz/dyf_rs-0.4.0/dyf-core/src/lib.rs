//! DYF Core - Density Yields Features
//!
//! PCA-based LSH for efficient density analysis of embedding spaces.
//!
//! Returns raw metrics per item - classification is left to the caller:
//! - bucket_id: LSH bucket assignment
//! - bucket_size: Number of items in the bucket
//! - centroid_similarity: Cosine similarity to bucket centroid (0-1)
//! - isolation_score: How isolated the item is (top_k_sim - median_sim)

mod density_classifier;

pub use density_classifier::{
    DensityClassifier, DensityReport, BridgeAnalysis,
    BitDepthStats, analyze_bit_depths, select_optimal_bit_depth,
};
