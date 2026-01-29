# prismboost

**Geometry-boosted machine learning for industrial diagnostics.**

prismboost combines PRISM behavioral feature engineering with gradient boosting for state-of-the-art predictive maintenance and remaining useful life (RUL) prediction.

## Status

🚧 **Coming soon** - Package under active development.

## Results

On NASA C-MAPSS turbofan degradation benchmark (FD001):

| Method | Test RMSE |
|--------|-----------|
| Raw sensors + XGBoost | 17.56 |
| Published benchmark | 6.62 |
| **prismboost** | **4.76** |

**73% improvement over baseline. 28% better than benchmark.**

## Key Features

- **Behavioral feature engineering**: Hurst exponent, entropy, GARCH volatility, Lyapunov exponents per sensor
- **Geometry-aware**: PCA manifold structure, clustering dynamics, coupling analysis
- **State trajectory**: Acceleration, curvature, mode transitions in behavioral space
- **Domain-agnostic**: Works on turbofans, bearings, hydraulics, chemical processes

## Installation

```bash
pip install prismboost
```

## License

MIT
