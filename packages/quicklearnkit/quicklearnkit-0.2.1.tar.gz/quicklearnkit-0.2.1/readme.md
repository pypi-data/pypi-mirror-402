````markdown
# QuickLearnKit

QuickLearnKit is a lightweight, learning-first machine learning utilities library designed to simplify model imports and streamline common ML workflows. No more deep module navigation—import models and tools effortlessly and start building.

It focuses on removing *mechanical friction* so students and practitioners can spend more time understanding concepts, not fighting syntax.

---

## Installation

Install QuickLearnKit using pip:

```bash
pip install quicklearnkit
````

---

## Quick Model Imports

QuickLearnKit provides seamless access to essential machine learning models with minimal syntax. Simply import and initialize models without the usual clutter.

### Example Usage

```python
from quicklearnkit import (
    LinearRegressionmodel,
    RandomForestRegressionmodel,
    XGBoostRegressionmodel,
    KNeighborsClassifiermodel,
    GradientBoostingClassifiermodel
)

# Initialize models directly
lr_model = LinearRegressionmodel()
rf_model = RandomForestRegressionmodel()
xgb_model = XGBoostRegressionmodel()

# Initialize classifiers
knn_classifier = KNeighborsClassifiermodel()
gb_classifier = GradientBoostingClassifiermodel()
```

---

## Supported Models

QuickLearnKit offers easy access to commonly used supervised learning models:

### Regression Models

* Linear Regression (`LinearRegressionmodel()`)
* K-Nearest Neighbors Regression (`KNNRegressionmodel()`)
* Decision Tree Regression (`DecisionTreeRegressionmodel()`)
* Random Forest Regression (`RandomForestRegressionmodel()`)
* Gradient Boosting Regression (`GradientBoostingRegressionmodel()`)
* AdaBoost Regression (`AdaBoostRegressionmodel()`)
* XGBoost Regression (`XGBoostRegressionmodel()`)
* ElasticNet Regression (`ElasticNetRegressionmodel()`)

### Classification Models

* Logistic Regression (`LogisticRegressionmodel()`)
* K-Nearest Neighbors Classifier (`KNeighborsClassifiermodel()`)
* Decision Tree Classifier (`DecisionTreeClassifiermodel()`)
* Random Forest Classifier (`RandomForestClassifiermodel()`)
* AdaBoost Classifier (`AdaBoostClassifiermodel()`)
* Gradient Boosting Classifier (`GradientBoostingClassifiermodel()`)
* XGBoost Classifier (`XGBClassifiermodel()`)
* Support Vector Classifier (`SVClassifiermodel()`)

---

## Utilities & Workflow Tools

Beyond models, QuickLearnKit provides practical tools to support the full machine learning workflow.

---

### 🔀 Random Sampling — `Sampler`

Randomly sample from lists, NumPy arrays, or pandas DataFrames. Supports both **stateless (reproducible)** and **stateful (streaming / simulation)** modes.

```python
from quicklearnkit import Sampler
import seaborn as sns

df = sns.load_dataset("titanic")

sampler = Sampler(df, n=5, random_state=42)
sampled_data = sampler.sample()

print(sampled_data)
```

---

### ✂️ Train–Test Splitting — `train_test_split`

Split datasets into training and testing sets with support for:

* Shuffling
* Stratification
* NumPy arrays and pandas DataFrames

```python
from quicklearnkit import train_test_split
import numpy as np

X = np.arange(20).reshape(10, 2)

X_train, X_test = train_test_split(
    X,
    test_size=0.25,
    shuffle=True,
    random_state=42
)

print(X_train.shape, X_test.shape)
```

---

### 🎲 Probabilistic Imputation — `ProbabilisticImputer`

A group-aware, probabilistic categorical imputer that learns conditional distributions and samples missing values in a **reproducible** way by default.

This is especially useful for:

* Teaching how distributions work
* Simulating realistic missing data handling
* Data augmentation and robustness testing

```python
from quicklearnkit import ProbabilisticImputer
import seaborn as sns

df = sns.load_dataset("titanic")

imputer = ProbabilisticImputer(
    group_col="pclass",
    target_col="deck",
    random_state=42  # reproducible by default
)

df_imputed = imputer.fit_transform(df)

print("Missing before:", df["deck"].isna().sum())
print("Missing after:", df_imputed["deck"].isna().sum())
```

---

## Randomized Data Generation

Generate random arrays with specific characteristics:

```python
from quicklearnkit import create_random

random_data = create_random(mean=0, std_dev=1, size=100)
print(random_data)
```

---

## Contribute

Want to improve QuickLearnKit? Fork the repository, suggest enhancements, and help make machine learning more accessible and easier to teach.

---

## License

This project is licensed under the MIT License.

---

QuickLearnKit makes machine learning utilities effortless—so you can focus on **learning, experimenting, and building**, not writing complex import statements. 🚀

````

