import warnings
from copy import deepcopy

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from fedrf4panod import federated_random_forest_helper as helper
from fedrf4panod import model_serializer as serializer


class FederatedRandomForestClassifier(RandomForestClassifier):
    """
    FederatedRandomForestClassifier extends sklearn.ensemble.RandomForestClassifier

    The purpose of this class is to provide a Random Forest implementation
    for aggregating different local random forest models into one federated
    model.

    Uniform model parameters (the initialization parameters of
    sklearn.ensemble.RandomForestClassifier) should be used to ensure
    that the models are trained in the same way.

    In addition, the FederatedRandomForest instance manages a global
    dictionary so that all decision trees of the FederatedRandomForest
    model have uniform column indices.

    """

    tree_aggregation_methods = ["add", "constant"]
    weighting_approaches = [None, "trees-per-sample-size-rate", "weighted-sampling"]

    def __init__(
        self,
        tree_aggregation_method: str,
        weighting: str = None,
        trees_per_sample_size_rate: float = None,
        **sk_learn_parameters,
    ):
        """
        Creates a Federated Random Forest model. To train the local models uniformly,
        init parameters of the `sklearn.ensemble.RandomForestClassifier` class are
        passed when a Federated Random Forest instance is created, as well as
        parameters to define the update procedure for the local models.

        Parameters
        ----------
        tree_aggregation_method: str
            Method for updating the local models, either "constant"
            (maintaining the number of trees) or "add" (extending with additional trees).

        weighting: str, optional
            Method for weighting the trees from different sites based on their local sample sizes.
            Must be either `trees-per-sample-size-rate` or `weighted-sampling`:

            - `trees-per-sample-size-rate`: Uses the `trees_per_sample_size_rate` parameter to determine
              how many trees should be trained at each site relative to its sample size.

            - `weighted-sampling`: During the update of the local model, assigns a sampling probability
              to each tree that reflects the differences in site sizes.

        trees_per_sample_size_rate: float, optional
            Should be set only when `weighting` is `trees-per-sample-size-rate`. This parameter
            determines the number of trees to be trained per sample at a given site. For example,
            if set to `2.0`, two trees will be trained for each sample at the local sites.

        **sk_learn_parameters: dict
            Parameters used to train the local random forest models, which are passed
            to the `sklearn.ensemble.RandomForestClassifier` constructor.
        """
        warnings.simplefilter("always")
        # Sets the strategy how the trees on the local sites should be combined
        self.tree_aggregation_method = helper.check_if_element_is_valid(
            element_to_check=tree_aggregation_method,
            valid_elements=self.tree_aggregation_methods,
            variable_name_to_check="tree_aggregation_method",
        )
        # Sets the weighting method
        self.weighting = helper.check_if_element_is_valid(
            element_to_check=weighting,
            valid_elements=self.weighting_approaches,
            variable_name_to_check="weighting",
        )
        # Set the trees to sample size rate for this weighting approach
        self.trees_per_sample_size_rate = (
            helper.set_trees_per_sample_size_rate_if_needed(
                weighting_method=weighting, rate=trees_per_sample_size_rate
            )
        )
        # Check if only valid aggregation methods are chosen for weighted sampling
        helper.check_aggregation_method_for_weighted_sampling(
            weighting_method=weighting, aggregation_method=tree_aggregation_method
        )
        # Retrieves the parameters that should be used for training the local models
        super().__init__(**sk_learn_parameters)
        self.sk_learn_parameters_dict = sk_learn_parameters
        self.federated_feature_mapping_dict = {}

    def get_training_parameters(self) -> dict[str, int]:
        """
        Retrieves the sklearn training parameters defined for training the
        random forests at the local sites.

        Returns
        -------
        dict[str, int]
            A dictionary where the keys are the names of the training parameters,
            and the values are the corresponding parameter values.
        """
        parameter_dict = self.sk_learn_parameters_dict
        return parameter_dict

    def update_federated_dictionary(
        self, local_feature_mapping_dict: dict[str, int]
    ) -> dict[str, int]:
        """
        Updates the federated feature mapping dictionary with new columns from the local feature
        mapping dictionary, if they are not already present.

        Parameters
        ----------
        local_feature_mapping_dict: dict[str, int]
            A dictionary where the keys are column names and the values are their corresponding IDs.

        Returns
        -------
        dict[str, int]
            The updated federated feature mapping dictionary, reflecting any new columns
            from the local feature mapping dictionary.
        """
        # Check if the dictionary is empty
        dict_is_empty = len(self.federated_feature_mapping_dict) == 0
        if dict_is_empty:
            # If empty just add every entry from local mapping
            self.federated_feature_mapping_dict = deepcopy(local_feature_mapping_dict)
        # If there are already some entries
        else:
            for local_column_name in local_feature_mapping_dict:
                # Check if we have a new column not present in the federated dictionary
                if local_column_name not in self.federated_feature_mapping_dict:
                    # Determine the next "free" ID for federated dictionary & replace
                    next_federated_col_index = len(self.federated_feature_mapping_dict)
                    self.federated_feature_mapping_dict[local_column_name] = (
                        next_federated_col_index
                    )
        return self.federated_feature_mapping_dict

    def update_federated_model(
        self,
        local_trees: list[DecisionTreeClassifier],
        local_feature_mapping: dict,
        local_model_has_committed: bool,
    ) -> None:
        """
        Updates the federated model by incorporating newly trained local trees.
        Replaces old trees from the local site if there are any.

        Parameters
        ----------
        local_trees: list[DecisionTreeClassifier]
            A list of `DecisionTreeClassifier` objects representing the trees from the local model.

        local_feature_mapping: dict[str, int]
            A dictionary mapping column names (keys) to their corresponding local IDs (values).

        local_model_has_committed: bool
            Indicates whether the local model has previously committed trees to the federated model.
        """
        # Update the federated model first with the new feature mapping dictionary
        self.update_federated_dictionary(local_feature_mapping)
        # Transform the indices used in the local trees to the indices from the federated model
        local_trees_using_federated_ids = (
            helper.transform_trees_to_different_feature_mapping(
                local_trees, local_feature_mapping, self.federated_feature_mapping_dict
            )
        )
        # If the given trees are the first ones committed to the federated model
        if not hasattr(self, "estimators_"):
            self.estimators_ = local_trees_using_federated_ids
            assert len(self.estimators_) == len(local_trees_using_federated_ids)
        # If already some trees have been added to the federated model
        else:
            # When some trees from this site are already available replace them
            if local_model_has_committed:
                updated_model = helper.replace_trees_with_same_id(
                    fed_trees=self.get_trees(),
                    local_trees=local_trees_using_federated_ids,
                )
                self.estimators_ = updated_model
            # Otherwise just add them to the federated model
            else:
                self.estimators_.extend(local_trees_using_federated_ids)

        return None

    def aggregate_local_models(
            self,
            local_models: list[tuple[list[DecisionTreeClassifier], dict[str, int]]]
    ) -> 'FederatedRandomForestClassifier':
        """
        Aggregates multiple local models into the federated model by incorporating their trees
        and feature mappings. This method creates a new federated model independent of any
        previous updates.

        Parameters
        ----------
        local_models: list[tuple[list[DecisionTreeClassifier], dict[str, int]]]
            A list of tuples, where each tuple contains:
            - A list of DecisionTreeClassifier objects representing the trees from a local model
            - A dictionary mapping column names to their corresponding local IDs for that model

        Returns
        -------
        FederatedRandomForestClassifier
            The updated federated model containing aggregated trees from all local models
        """
        # Reset the federated model's state
        self.estimators_ = []
        self.federated_feature_mapping_dict = {}

        # Process each local model
        for local_model in local_models:
            local_trees = deepcopy(local_model.get_trees())
            local_feature_mapping = deepcopy(local_model.local_feature_mapping)
            # Update federated dictionary with new features from this local model
            self.update_federated_dictionary(local_feature_mapping)

            # Transform local trees to use federated feature IDs
            local_trees_using_federated_ids = helper.transform_trees_to_different_feature_mapping(
                local_trees,
                local_feature_mapping,
                self.federated_feature_mapping_dict
            )

            if self.weighting == "weighted-sampling":
                # Apply weighted sampling if specified
                sampled_trees = helper.sample_trees_using_weighting(
                    trees=local_trees_using_federated_ids,
                    number_of_local_trees=len(local_trees),
                    random_state=self.random_state
                )
                self.estimators_.extend(sampled_trees)
            elif self.tree_aggregation_method == "constant":
                # For constant aggregation, sample equal number of trees from each model
                min_trees = min(len(local_trees_using_federated_ids) for local_trees, _ in local_models)
                sampled_trees = helper.sample_trees(
                    trees=local_trees_using_federated_ids,
                    n=min_trees,
                    random_state=self.random_state
                )
                self.estimators_.extend(sampled_trees)
            else:  # "add" aggregation method
                # Add all trees from this model
                self.estimators_.extend(local_trees_using_federated_ids)

            # Remove any site-specific information from the trees
            self.estimators_ = helper.delete_site_info_from_trees(self.estimators_)

        return self


    def get_trees(self) -> list[DecisionTreeClassifier]:
        """
        Retrieves all trees currently in the federated model.

        Returns
        -------
        list[DecisionTreeClassifier]
            A list of all trees in the federated model, with their feature indices
            mapped to the federated column IDs. If no trees are present, returns None.
        """
        if hasattr(self, "estimators_"):
            return deepcopy(self.estimators_)
        else:
            return None

    def get_trees_for_updating_local_model(
        self, number_of_local_trees: int, local_feature_mapping: dict, random_state: int
    ) -> list[DecisionTreeClassifier]:
        """
        Provides the updated model to the local site by adapting the aggregated trees
        from the federated model to the local feature schema. Non-transferable trees
        are removed. If a weighting method has been defined, it is applied
        during the update process.

        Parameters
        ----------
        number_of_local_trees: int
            The number of trees at the local site.

        local_feature_mapping: dict[str, int]
            A dictionary mapping the local column IDs to their corresponding feature names.

        random_state: int
            An optional integer specifying the random state for reproducibility.

        Returns
        -------
        list[DecisionTreeClassifier]
            A list of `DecisionTreeClassifier` objects representing the updated trees
            adapted to the local site, with non-transferable trees removed and
            site-specific information deleted. If a weighting method has been defined,
            the updated trees will reflect the applied weighting.
        """
        federated_feature_mapping = self.get_feature_mapping()
        federated_trees = self.get_trees()
        # Transform trees to the local variable encoding
        updated_trees = helper.transform_trees_to_different_feature_mapping(
            federated_trees, federated_feature_mapping, local_feature_mapping
        )
        # Do constant aggregation when `weighted-sampling` shouldn't be done
        if (
            self.tree_aggregation_method == "constant"
            and self.weighting != "weighted-sampling"
        ):
            # Sample trees for constant aggregation
            updated_trees = helper.sample_trees(
                trees=updated_trees,
                n=number_of_local_trees,
                random_state=self.random_state,
            )
        if self.weighting == "weighted-sampling":
            updated_trees = helper.sample_trees_using_weighting(
                trees=updated_trees,
                number_of_local_trees=number_of_local_trees,
                random_state=self.random_state,
            )
        # Delete all site information before sending the updated model back to the local site
        updated_trees = helper.delete_site_info_from_trees(updated_trees)
        return updated_trees

    def get_feature_mapping(self) -> dict[str, int]:
        """
        Retrieves the current feature mapping dictionary used by the federated model.

        Returns
        -------
        dict[str, int]
            A dictionary mapping column names (keys) to their corresponding federated
            column IDs (values).
        """
        federated_feature_mapping = self.federated_feature_mapping_dict
        return deepcopy(federated_feature_mapping)

    def save_model(self, file_name: str = None ,save_location_path: str = None) -> None:
        """
        Saves the current model instance to a pickle file.

        Parameters
        ----------
        file_name: str
            The name of the file (without extension) to be created for saving the model.

        save_location_path: str, optional
            The path to the directory where the file will be saved. Defaults to None.
            If None, the file is saved to a sub-folder within the current working
            directory, as determined by the default configuration.
        """
        if not file_name:
            file_name = save_location_path.split("/")[-1]
            save_location_path = save_location_path.replace(file_name, "")

        if ".pkl" in file_name:
            file_name = file_name.replace(".pkl", "")

        serializer.save_object(
            self, file_name, "federated_rf_files", save_location_path
        )

    @classmethod
    def load_model(cls, file_path: str) -> 'FederatedRandomForestClassifier':
        """
        Loads a `FederatedRandomForest` model from a pickle file located at the specified path.

        Parameters
        ----------
        file_path: str
            The path to the file containing the serialized model data.

        Returns
        -------
        object
            An instance of the `FederatedRandomForest` class loaded from the file.
        """
        return serializer.load_object(cls, file_path)

    def predict(self, X) -> NotImplementedError:
        """
        Predict method is not available for the `FederatedRandomForest` model.

        Since there is no common data model across sites due to overlapping features,
        the `predict()` method is not implemented for the federated model. Prediction
        should be performed at the respective local sites after updating the local model
        to utilize the optimized federated silo-specific local model.

        Raises
        ------
        NotImplementedError
            Always raised, indicating that `predict()` is not available for the federated model.
        """
        raise NotImplementedError(
            f"predict() is not available for the FederatedRandomForest model.\n\n"
            f"Please use predict(use_updated_federated_model=True) at the respective \n"
            f"site after updating the local model in order to use the optimized federated \n"
            f"silo-specific local model."
        )

    def predict_proba(self, X) -> NotImplementedError:
        """
        Predict_proba method is not available for the `FederatedRandomForest` model.

        Due to the lack of a common data model across sites, the `predict_proba()` method
        is not implemented for the federated model. Probability prediction should be
        conducted at the local sites after updating the local model to leverage the
        optimized federated silo-specific local model.

        Raises
        ------
        NotImplementedError
            Always raised, indicating that `predict_proba()` is not available for the federated model.
        """
        raise NotImplementedError(
            f"predict_proba() is not available for the FederatedRandomForest model.\n\n"
            f"Please use predict_proba(use_updated_federated_model=True) at the respective \n"
            f"site after updating the local model in order to use the optimized federated \n"
            f"silo-specific local model."
        )

    def predict_log_proba(self, X) -> NotImplementedError:
        """
        Predict_log_proba method is not available for the `FederatedRandomForest` model.

        As there is no unified data model across sites, the `predict_log_proba()` method
        is not implemented for the federated model. Log probability prediction should be
        done at the local sites after updating the local model to utilize the optimized
        federated silo-specific local model.

        Raises
        ------
        NotImplementedError
            Always raised, indicating that `predict_log_proba()` is not available for the federated model.
        """
        raise NotImplementedError(
            f"predict_log_proba() is not available for the FederatedRandomForest model.\n\n"
            f"Please use predict_log_proba(use_updated_federated_model=True) at the respective \n"
            f"site after updating the local model in order to use the optimized federated \n"
            f"silo-specific local model."
        )

    def fit(self, X, y, sample_weight=None) -> NotImplementedError:
        """
        Fit method is not available for the `FederatedRandomForest` model.

        The `FederatedRandomForest` model is designed to aggregate trees rather than
        creating new ones. Therefore, the `fit()` method is not implemented. To train
        local random forest models, use `fit()` at the respective sites, and then
        aggregate the trees into the federated model.

        Raises
        ------
        NotImplementedError
            Always raised, indicating that `fit()` is not available for the federated model.
        """
        raise NotImplementedError(
            f"fit() is not available for the FederatedRandomForest model.\n\n"
            f"Please use fit() at the respective site in order to train site-specific \n"
            f"local random forest models. FederatedRandomForest is intended to aggregate \n"
            f"all trees instead of creating new ones."
        )
