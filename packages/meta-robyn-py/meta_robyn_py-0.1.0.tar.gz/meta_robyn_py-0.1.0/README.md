
# Robyn Python

A Python implementation of **Robyn**, an experimental, automated and open-sourced Marketing Mix Modeling (MMM) code by Meta Marketing Science.

This package aims to be a feature-complete port of the original R package, providing the same automated hyperparameter optimization, ridge regression modeling, and budget allocation capabilities.

## Features

*   **Automated Hyperparameter Optimization**: Uses `Nevergrad` to efficiently explore adstock, saturation, and regularization parameters.
*   **Ridge Regression**: Constrained ridge regression to ensure valid coefficient signs.
*   **Feature Engineering**: Integrated Prophet decomposition for trend, seasonality, and holiday effects.
*   **Multi-Objective Optimization**: Optimizes for NRMSE and DECOMP.RSSD (Business Logic) to find Pareto-optimal models.
*   **Budget Allocation**: Non-linear optimization to maximize response given budget constraints.

## Installation

```bash
pip install meta-robyn-py
```
*(Note: If not yet on PyPI, install locally)*
```bash
pip install .
```

## Quick Start

```python
import pandas as pd
from robyn import robyn_inputs, robyn_run, robyn_outputs, robyn_allocator

# 1. Load Data
dt_input = pd.read_csv("your_data.csv")
dt_holidays = pd.read_csv("holidays.csv")

# 2. Configure Inputs
input_collect = robyn_inputs(
    dt_input=dt_input,
    dt_holidays=dt_holidays,
    date_var="DATE",
    dep_var="revenue",
    dep_var_type="revenue",
    prophet_vars=["trend", "season", "holiday"],
    prophet_country="DE",
    context_vars=["competitor_sales", "events"],
    paid_media_spends=["tv_S", "facebook_S"],
    paid_media_vars=["tv_S", "facebook_I"],
    organic_vars=["newsletter"],
    window_start="2016-11-23",
    window_end="2018-08-22",
    adstock="geometric"
)

# 3. Add Hyperparameters
hyperparameters = {
    "tv_S_alphas": [0.5, 3], "tv_S_gammas": [0.3, 1], "tv_S_thetas": [0, 0.3],
    "facebook_I_alphas": [0.5, 3], "facebook_I_gammas": [0.3, 1], "facebook_I_thetas": [0, 0.3],
    "train_size": [0.5, 0.8]
    # ... add for others
}
input_collect = robyn_inputs(InputCollect=input_collect, hyperparameters=hyperparameters)

# 4. Run Model
output_models = robyn_run(
    InputCollect=input_collect,
    iterations=2000,
    trials=5,
    outputs=False
)

# 5. Export Results & Clusters
output_collect = robyn_outputs(
    input_collect=input_collect,
    output_models=output_models,
    pareto_fronts="auto",
    clusters=True,
    export=True
)

# 6. Budget Allocation
best_model = output_collect['clusters']['models'].iloc[0]['solID']
allocator = robyn_allocator(
    input_collect=input_collect,
    output_collect=output_collect,
    select_model=best_model,
    scenario="max_response",
    channel_constr_low=0.7,
    channel_constr_up=1.2
)
```

## Comparisons with R version

This Python port has been benchmarked against the R version using standard simulation data.

| Metric | Python Port | R Reference |
| :--- | :--- | :--- |
| **NRMSE** | **0.0442** | ~0.04 - 0.06 |
| **Speed** | ~96 iter/s | ~50 - 100 iter/s |

See `COMPARISON_REPORT.md` for full details.

## License

MIT
