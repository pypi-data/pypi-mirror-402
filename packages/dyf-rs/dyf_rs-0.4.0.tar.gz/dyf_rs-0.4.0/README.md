# DYF-RS - Density Yields Features (Rust Core)

Rust-accelerated core for DYF. Discover structure in embedding spaces using density-based LSH.

- **Dense**: Core items in well-populated semantic regions
- **Bridge**: Transitional items connecting different clusters
- **Orphan**: Unique items with no semantic neighbors

## Installation

```bash
pip install dyf-rs
```

For the full Python package with serialization, embedding generation, and LLM labeling:
```bash
pip install dyf
```

## Quick Start

```python
import numpy as np
from dyf_rs import DensityClassifier

# Your embeddings (e.g., from sentence-transformers)
embeddings = np.random.randn(10000, 384).astype(np.float32)

# Find structure
classifier = DensityClassifier(embedding_dim=384)
classifier.fit(embeddings)

# What did we find?
print(classifier.report())
# Corpus: 10000 items
#   Dense: 9500 (95.0%)
#   Bridge: 450 (4.5%)
#   Orphan: 50 (0.5%)

# Get indices
bridges = classifier.get_bridge()  # Transitional items
orphans = classifier.get_orphans() # Unique items
```

## Performance

| Dataset | Time | Per item |
|---------|------|----------|
| 60K embeddings (384d) | ~60ms | 1.0 µs |

~4x faster than pure Python/sklearn.

## API

### DensityClassifier

```python
DensityClassifier(
    embedding_dim: int,
    initial_bits: int = 14,      # LSH resolution
    recovery_bits: int = 8,      # Coarser recovery resolution
    dense_threshold: int = 10,   # Min bucket size for "dense"
    seed: int = 31
)

# Methods
classifier.fit(embeddings)
classifier.fit_arrow(arrow_array)  # Zero-copy from PyArrow
classifier.get_dense()             # Dense item indices
classifier.get_bridge()            # Bridge item indices
classifier.get_orphans()           # Orphan item indices
classifier.get_bucket_id(idx)      # Which bucket is item in?
classifier.report()                # Summary statistics
```

## See Also

- [dyf](https://github.com/jdonaldson/dyf) - Full Python package with serialization, configs, and LLM labeling
- [Curvo FDA Navigator](https://huggingface.co/spaces/jdonaldson/curvo-fda-navigator) - DYF in action on 2.69M FDA medical devices

## License

Proprietary
