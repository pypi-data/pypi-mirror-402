# ABOBA

AB tests library with simplicity in mind

## 📚 Documentation

- **[Full Documentation](https://ab-alexroar-8e192a9a66171262804e0b0f9c942db31bc9c224aebd3d3d415.gitlab.io)** - Complete guide and reference
- **[Tutorial](https://ab-alexroar-8e192a9a66171262804e0b0f9c942db31bc9c224aebd3d3d415.gitlab.io/tutorial/)** - Step-by-step learning guide
- **[API Reference](https://ab-alexroar-8e192a9a66171262804e0b0f9c942db31bc9c224aebd3d3d415.gitlab.io/api/tests/)** - Detailed API documentation

## ✨ Features

- **Simple & Intuitive API** - Easy to learn and use for both beginners and experts
- **Multiple Statistical Tests** - t-tests, ANOVA, Kruskal-Wallis, and more
- **Variance Reduction** - Built-in CUPED, stratification, and regression adjustments
- **Power Analysis** - Simulate synthetic effects to estimate required sample sizes
- **Flexible Pipelines** - Chain data processors and samplers for complex workflows
- **Experiment Orchestration** - Run and visualize multiple test scenarios simultaneously
- **Extensible Architecture** - Easy to create custom tests, samplers, and processors
- **Production Ready** - Type hints, comprehensive tests, and detailed documentation

## 🚀 Quick Start

### Installation

```bash
pip install aboba
```

## 📖 Quick Example

To conduct a test, you need several entities:

- data
- data processing
- data sampling technique
- the test strategy itself

Data can be a simple pandas dataframe or custom data generator. 

### General use case

```python
import numpy as np
import pandas as pd
import scipy.stats as sps

from aboba import (
    tests,
    samplers,
    effect_modifiers,
    experiment,
)
from aboba.pipeline import Pipeline

# Create dataset with two groups
data = pd.DataFrame({
    'value'  : np.concatenate([
        sps.norm.rvs(size=1000, loc=0, scale=1),
        sps.norm.rvs(size=1000, loc=0, scale=1),
    ]),
    'is_b_group': np.concatenate([
        np.repeat(0, 1000),
        np.repeat(1, 1000),
    ]),
})

# Configure test
test = tests.AbsoluteIndependentTTest(
    value_column='value',
)

# Create pipeline with sampler
sampler = samplers.GroupSampler(
    column='is_b_group',
    size=100,
)
pipeline = Pipeline([
    ('sampler', sampler),
])

# Run experiment
n_iter = 500
exp = experiment.AbobaExperiment(draw_cols=1)

group_aa = exp.group(
    name="AA, regular",
    test=test,
    data=data,
    data_pipeline=pipeline,
    n_iter=n_iter
)
group_aa.run()

effect = effect_modifiers.GroupModifier(
    effects={1: 0.3},
    value_column='value',
    group_column='is_b_group',
)

group_ab = exp.group(
    name="AB, regular, effect=0.3",
    test=test,
    data=data,
    data_pipeline=pipeline,
    synthetic_effect=effect,
    n_iter=n_iter
)
group_ab.run()

# Draw results
fig, axes = exp.draw()
fig.savefig('results.png')
```

## 🎯 Key Components

- **Tests** - Statistical tests for hypothesis testing (t-tests, ANOVA, etc.)
- **Samplers** - Control how data is split into groups (random, stratified, grouped)
- **Processors** - Transform data before testing (CUPED, bucketing, normalization)
- **Pipelines** - Chain multiple processors and samplers together
- **Effect Modifiers** - Simulate synthetic effects for power analysis
- **Experiments** - Orchestrate multiple test runs and visualize results

## 📊 Use Cases

- **A/B Testing** - Compare two variants to determine which performs better
- **Multivariate Testing** - Test multiple variants simultaneously
- **Power Analysis** - Determine required sample sizes for detecting effects
- **Variance Reduction** - Use CUPED or stratification to improve test sensitivity
- **Custom Tests** - Implement domain-specific statistical tests

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details
