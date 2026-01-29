# FedRF4PaNOD

This package adapts scikit-learn's Random Forest algorithm for Federated Learning, specifically designed for cases where data is distributed across multiple sites with only partially overlapping features. It allows users to investigate how Federated Random Forest models perform under these conditions. The package includes various aggregation and weighting techniques for further experimentation and evaluation.

We recently demonstrated the application of this package in our latest publication, which is available [here](https://arxiv.org/abs/2405.20738).

The example code for (simulated) federated random forest analysis can be found in [this repository](https://gitlab.gwdg.de/cdss/fairpact/fedrf4panod).

## Installation

For creating a local source code distribution of the current code, the following command can be used:

```bash
python setup.py sdist bdist_wheel  
```

Currently, the module can be installed locally using the package manager [pip](https://pip.pypa.io/en/stable/) and the local distribution file, created by the previously stated command:

```bash
pip install ./dist/fedrf4panod-0.0.2.tar.gz
```

## Usage

### Getting Started

Initially, a federated model is created to manage the process of collecting and aggregating the trees. At each site, local random forests are then trained independently and the resulting models are sent to the federated model. The federated model aggregates all trees from the various sites. This aggregation allows each local model to be updated by incorporating all trees with matching features from other sites, resulting in an updated local model (federated silo-specific local model) that benefits from the knowledge shared across all participating sites:

![FederatedRandomForestforPNOD.png](figures%2FFederatedRandomForestforPNOD.png)

#### 1. Initialize the Federated Model

To aggregate trees from the local sites, an instance of the `FederatedRandomForestClassifier` has to be created:

```python
from fedrf4panod.federated_random_forest_classifier.federated_random_forest_cls import FederatedRandomForestClassifier
from fedrf4panod.federated_random_forest_classifier.local_random_forest_cls import LocalRandomForestClassifier

# Initialize federated model
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add", n_estimators=100)
```

For this, the `tree_aggregation_method` must be specified. Optionally, parameters of `sklearn.ensemble.RandomForestClassifier` can also be set to define the training setup for all local models.

For regression tasks `FederatedRandomForestRegressor` & `LocalRandomForestRegressor` can be used analogously:

```python
from fedrf4panod.federated_random_forest_regressor.federated_random_forest_reg import FederatedRandomForestRegressor
from fedrf4panod.federated_random_forest_regressor.local_random_forest_reg import LocalRandomForestRegressor

# Initialize federated model
fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add", n_estimators=100)
```

#### 2. Train and Commit Local Model

To make the local model available to other sites, the trained local model has to be committed to the federated model:

```python
local_rf = LocalRandomForestClassifier(fed_rf) # Initialize local model
local_rf.fit(X_train, y_train) # Train local model
local_rf.commit_local_random_forest() # Commit local model to federated model

# Train and commit other local models in the same way
local_rf2 = ...
```

The training process is analogous to the training process of  the `sklearn.ensemble.RandomForestClassifier`.

#### 3. Update the Local Model

After the other local models have been committed, the local model can be updated with all matching trees from the aggregated federated model:

```python
local_rf.get_updated_trees_from_federated_model()
```

#### 4. Use the Updated Model for Prediction

The updated model can then be used for making predictions by setting `use_updated_federated_model=True`:

```python
prediction_updated_model = local_rf.predict(X_test, use_updated_federated_model=True) # Make predictions with updated model
```

### Aggregation Methods: Add & Constant Aggregation

When updating local models using the federated model, two aggregation techniques are available:

**Add Aggregation:** 
In this approach, all trees from the federated model that have matching features with the local site are transferred to the updated local model. This method ensures that the local model benefits from all potentially relevant trees, which means that the number of trees in the local model increases if matching trees are found. Consequently, the number of trees can vary across different sites after updating. To initialize the federated model with add aggregation `tree_aggregation_method` has to be set accordingly:
```python
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add")
```

**Constant Aggregation:** 
In this approach, a sample of trees from the federated model is selected to match the initial number of trees in the local model. This ensures that the updated local model maintains a size comparable to the initial local model, preserving consistency in model dimensions. However, since only a subset of matching trees is used, some information may be lost in the process, as not all trees are included in the updated local model. To initialize the federated model with constant aggregation `tree_aggregation_method` has to be set accordingly:
```python
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="constant")
```

### Model Weighting: Weighted Sampling & Rate-Based Weighting

To address the differences in sample sizes across sites and ensure that sites with larger sample sizes have a proportionate impact on the federated model, two weighting schemes are available:

**Rate-Based Weighting:**
This method adjusts the number of trees trained at local sites based on the rate of trees per sample. By setting the rate during initialization, it is ensured that sites with larger sample sizes contribute a larger number of trees to the federated model. For instance, with a rate of 0.5, one tree is trained for every two samples. To use rate-based weighting, the Federated Random Forest has to be initialized as follows:
```python
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add", weighting="trees-per-sample-size-rate", trees_per_sample_size_rate=0.5)
```

**Weighted Sampling:**
This approach applies exact weighting during the update process of the local model. The sampling probability for each tree that can be transferred to the local site is calculated using:

$$
p_{ij} = \frac{n_{\text{samples}}}{n_{\text{total}} \cdot n_{\text{trees}}}
$$

where $n_{\text{samples}}$ is the number of samples at the local site $i$, $n_{\text{total}}$ is the total number of samples across all sites, and $n_{\text{trees}}$ is the number of transferable trees originating from site $i$. This ensures that the number of trees from a specific site in the updated local model is proportional to the site's sample size. To use weighted sampling, initialize the Federated Random Forest with:

```python
fed_rf = FederatedRandomForestClassifier(weighting="weighted-sampling", tree_aggregation_method="constant")
```
Note that `tree_aggregation_method` must be set to `"constant"` when using weighted sampling.

### Load / Save Model
Local Random Forest and Federated Random Forest models can be saved and loaded using the following methods:

To save a model:
```python
local_rf_1.save_model(file_name="local_rf_1")
fed_rf.save_model(filename="fed_rf")
```
This will create pickled files of the model states.

To load a model from a file:
```python
loaded_rf = LocalRandomForestClassifier.load_model(file_path)
loaded_fed_rf = FederatedRandomForestClassifier.load_model(file_path)
```


### Saved models aggregation

To aggregate saved models, the following method can be used:
```python
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add")
fed_rf = fed_rf.load_model(fed_rf_path)

local_rf = LocalRandomForestClassifier(fed_rf)
local_rf = local_rf.load_model(local_rf_path)

local_preds = local_rf.predict(X_test, use_updated_federated_model=False)
local_rf.commit_local_random_forest() # this is necessary to update the initialized local model (FederatedRandomForestClassifier) with the trees from the saved local model file
local_rf.get_updated_trees_from_federated_model()
updated_local_preds = local_rf.predict(X_test, use_updated_federated_model=True)
```

### Reproducibility

Reproducibility can be ensured by setting the scikit-learn parameter `random_state` parameter during the initialization of the Federated Random Forest:
```python
fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add", random_state=42)
```
Setting `random_state` ensures that both the random forest training (tree generation), as well as the constant tree aggregation and weighted sampling, will be reproducible.
## Unittests

To verify functionality after code changes, all unittests can be executed by running [run_tests.py](tests%2Frun_tests.py). All unittests can be found [here](tests).


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Acknowledgements

This project makes use of [scikit-learn](https://scikit-learn.org/), specifically it extends the classes [RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html#sklearn.ensemble.RandomForestClassifier) as well as [RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html) to the federated setting. Furthermore, for testing some of the [toy datasets](https://scikit-learn.org/stable/datasets/toy_dataset.html) were used in [test_data](tests%2Ftest_data). 

Scikit-learn is an open-source library licensed under the BSD 3-Clause License. For more details, please refer to the [scikit-learn license](LICENSE_scikit-learn).

## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) License. See the [LICENSE](LICENSE) file for details.