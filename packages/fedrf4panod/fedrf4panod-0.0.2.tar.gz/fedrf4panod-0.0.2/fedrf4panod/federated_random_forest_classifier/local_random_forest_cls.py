import uuid
import warnings
from copy import deepcopy

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from . import FederatedRandomForestClassifier
from fedrf4panod import local_random_forest_helper as helper
from fedrf4panod import model_serializer as serializer


class LocalRandomForestClassifier(RandomForestClassifier):
    """
    LocalRandomForestClassifier extends sklearn.ensemble.RandomForestClassifier

    The purpose of this class is to provide a random forest implementation
    for a local site in the federated setting.

    The aim is that the model can be locally trained aligned with the
    training scheme in the federation setting, as well as being able
    to send their local trees to the federation model (using consistent
    variable encoding on the federation site) and further update its
    own model once a suitable federated model is available.
    """

    def __init__(self,
                federated_random_forest: FederatedRandomForestClassifier,
                site_id: str = None,
                n_estimators: int = 100,
                criterion: str = "gini",
                max_depth: int = None,
                min_samples_split: int = 2,
                min_samples_leaf: int = 1,
                min_weight_fraction_leaf: float = 0.0,
                max_features: str = None,
                max_leaf_nodes: int = None,
                min_impurity_decrease: float = 0.0,
                bootstrap: bool = True,
                oob_score: bool = False,
                n_jobs: int = None,
                random_state: int = None,
                verbose: int = 0,
                warm_start: bool = False,
                class_weight = None,
                ccp_alpha: float = 0.0,
                max_samples = None,
                monotonic_cst = None):
        """
        Initializes an instance for a local site within a federated setting.

        This constructor sets up a local model by referencing a `FederatedRandomForestClassifier`
        instance, which is used to ensure consistency and facilitate the aggregation of local models
        into the federated model.

        Parameters
        ----------
        federated_random_forest: FederatedRandomForestClassifier
            An instance of `FederatedRandomForestClassifier` that provides the training parameters
            for all local models and manages the aggregation of the federated model.

        params: dict
            A dictionary containing the parameters for the `RandomForestClassifier` model.

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
        """
        warnings.simplefilter("always")
        # Check if we have a FederatedRandomForest object
        if not isinstance(federated_random_forest, FederatedRandomForestClassifier):
            raise TypeError(
                f"LocalRandomForestClassifier requires an FederatedRandomForestClassifier, got "
                f"{type(federated_random_forest)} instead."
            )

        self.params = {
            "n_estimators": n_estimators,
            "criterion": criterion,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "min_weight_fraction_leaf": min_weight_fraction_leaf,
            "max_features": max_features,
            "max_leaf_nodes": max_leaf_nodes,
            "min_impurity_decrease": min_impurity_decrease,
            "bootstrap": bootstrap,
            "oob_score": oob_score,
            "n_jobs": n_jobs,
            "random_state": random_state,
            "verbose": verbose,
            "warm_start": warm_start,
            "class_weight": class_weight,
            "ccp_alpha": ccp_alpha,
            "max_samples": max_samples,
            "monotonic_cst": monotonic_cst
        }

        # Initializing basic values
        self.predict_proba_called_by_outside_function = False
        self.local_feature_mapping = None
        self.site_size = None
        self.model_is_trained = False
        self.has_committed = False
        # Set the reference to the federated model
        self.federated_random_forest = federated_random_forest

        # Retrieve the weighting scheme
        self.weighting = self.federated_random_forest.weighting
        # Retrieve the trees-per-sample rate for the corresponding weighting approach
        self.trees_per_sample_size_rate = (
            self.federated_random_forest.trees_per_sample_size_rate
        )
        # Get the tree aggregation method from the federated setting
        self.tree_aggregation_method = federated_random_forest.tree_aggregation_method

        # Force to use updated tree
        self.force_use_updated_tree = False
        # Use sklearn.ensemble.RandomForestClassifier __init__ with the given
        # parameters and initialize for training
        super().__init__(**self.params)
        # Generate a unique site-id based on uuid4 (random numbers)
        if site_id:
            self.site_id = site_id
        else:
            self.site_id = str(uuid.uuid4())

        # Extract parameters from the federated model if they are set
        self.n_estimators = getattr(self.federated_random_forest, 'n_estimators', self.n_estimators)
        self.random_state = getattr(self.federated_random_forest, 'random_state', self.random_state)
        if self.max_features is None:
            self.max_features = getattr(self.federated_random_forest, 'max_features', self.max_features)
        self.max_depth = getattr(self.federated_random_forest, 'max_depth', self.max_depth)

    def __getstate__(self):
        """
        Custom serialization method to ensure all necessary attributes are saved.
        """
        state = self.__dict__.copy()
        # Ensure critical attributes are included
        critical_attrs = {
            'copy_of_local_trees': getattr(self, 'estimators_', None),
            'local_feature_mapping': self.local_feature_mapping,
            'has_committed': self.has_committed
        }
        state.update(critical_attrs)
        return state

    def __setstate__(self, state):
        """
        Custom deserialization method to restore all attributes.
        """
        # Restore the copy of local trees if it exists
        if 'copy_of_local_trees' in state:
            self.estimators_ = state.pop('copy_of_local_trees')

        # Initialize the base RandomForestClassifier
        self.__dict__.update(state)

    def _force_use_updated_federated_model(self, flag=True):
        self.force_use_updated_tree = flag

        self.estimators_ = helper.select_correct_model_for_prediction(
            self, flag
        )

    def fit(self, X: pd.DataFrame, y, sample_weight=None):
        """
        Fits the local model to the provided training data in the federated setting.

        This method overrides the `fit()` method from `sklearn.ensemble.RandomForestClassifier` to adapt it for
        the federated environment. It builds a forest of trees based on the training set (X, y), generates feature
        mappings according to the training data, and configures the model according to federated settings. It further
        adjusts the number of trees to be trained based on the specified weighting method, if applicable.


        Parameters
        ----------
        X: {array-like, sparse matrix} of shape (n_samples, n_features)
            The training input samples. Internally, its dtype will be converted
            to ``dtype=np.float32``. If a sparse matrix is provided, it will be
            converted into a sparse ``csc_matrix``.

        y: array-like of shape (n_samples,) or (n_samples, n_outputs)
            The target values (class labels in classification, real numbers in
            regression).

        sample_weight: array-like of shape (n_samples,), default=None
            Sample weights. If None, then samples are equally weighted. Splits
            that would create child nodes with net zero or negative weight are
            ignored while searching for a split in each node. In the case of
            classification, splits are also ignored if they would result in any
            single class carrying a negative weight in either child node.

        Returns
        -------
        self: object
            Fitted estimator.
        """
        # Check if y is a Pandas Series
        if isinstance(y, pd.Series):
            # Conversion prevents pandas warnings to occur
            y = y.to_numpy()
        self.local_feature_mapping = helper.generate_feature_mapping(X)
        self.site_size = helper.determine_site_size(X)
        # Check for small number of trees in rate-based weighting
        helper.check_if_weighted_number_of_trees_is_not_too_small(
            weighting_method=self.weighting,
            site_size=self.site_size,
            rate=self.trees_per_sample_size_rate,
        )
        # Adjust number of trees to train according to site size in rate-based weighting
        if self.weighting == "trees-per-sample-size-rate":
            weighted_number_of_trees = (
                helper.determine_adjusted_number_of_trees_for_rate_based_weighting(
                    rate=self.trees_per_sample_size_rate, n=self.site_size
                )
            )
            self.n_estimators = weighted_number_of_trees
        # Train the local model
        fitted_model = super().fit(X, y, sample_weight)
        # Annotate trees with the site size for weighted sampling
        if self.weighting == "weighted-sampling":
            self.estimators_ = helper.annotate_trees_with_attribute(
                trees=self.estimators_,
                attribute_name="site_size",
                attribute_value=self.site_size,
            )
        # Annotate trees with the site ID
        self.estimators_ = helper.annotate_trees_with_attribute(
            trees=self.estimators_,
            attribute_name="site_id",
            attribute_value=self.site_id,
        )
        self.local_estimators_ = deepcopy(self.estimators_)
        self.model_is_trained = True
        return deepcopy(fitted_model)

    def predict(self, X, use_updated_federated_model: bool = False):
        """
        Overrides the predict()-method from sklearn.ensemble.RandomForestClassifier
        in order to adapt it to the federated setting. Enables the prediction using the
        optimized federated silo-specific local model when use_updated_federated_model is set to True.

        Predict class for X.The predicted class of an input sample is a vote by the trees in
        the forest, weighted by their probability estimates. That is,
        the predicted class is the one with highest mean probability
        estimate across the trees.

        Parameters
        ----------
        X: {array-like, sparse matrix} of shape (n_samples, n_features)
            The input samples. Internally, its dtype will be converted to
            ``dtype=np.float32``. If a sparse matrix is provided, it will be
            converted into a sparse ``csr_matrix``.

        Returns
        -------
        y: ndarray of shape (n_samples,) or (n_samples, n_outputs)
            The predicted classes.
        """
        # Setting this class variable is needed to prevent the model from changing self.estimators_
        # again when super().predict() calls predict_proba()
        self.predict_proba_called_by_outside_function = True
        # Set correct model for prediction
        if self.force_use_updated_tree:
            use_updated_federated_model = True

        self.estimators_ = helper.select_correct_model_for_prediction(
            self, use_updated_federated_model
        )
        preds = super().predict(X)
        self.predict_proba_called_by_outside_function = False
        return preds

    def predict_proba(self, X, use_updated_federated_model: bool = False):
        """
        Overrides the predict_proba()-method from sklearn.ensemble.RandomForestClassifier
        in order to adapt it for the federation setting. Enables the prediction using the
        optimized federated silo-specific local model when use_updated_federated_model is set to True.

        Predict class probabilities for X.

        The predicted class probabilities of an input sample are computed as
        the mean predicted class probabilities of the trees in the forest.
        The class probability of a single tree is the fraction of samples of
        the same class in a leaf.

        Parameters
        ----------
        X: {array-like, sparse matrix} of shape (n_samples, n_features)
            The input samples. Internally, its dtype will be converted to
            ``dtype=np.float32``. If a sparse matrix is provided, it will be
            converted into a sparse ``csr_matrix``.

        Returns
        -------
        p: ndarray of shape (n_samples, n_classes), or a list of such arrays
            The class probabilities of the input samples. The order of the
            classes corresponds to that in the attribute :term:`classes_`.
        """
        # Checks if predict() called predict_proba() in order to prevent multiple changing of
        # self.estimators_ for one prediction
        if not self.predict_proba_called_by_outside_function:
            # Set correct model for prediction
            if self.force_use_updated_tree:
                use_updated_federated_model = True

            self.estimators_ = helper.select_correct_model_for_prediction(
                self, use_updated_federated_model
            )
        return super().predict_proba(X)

    def predict_log_proba(self, X, use_updated_federated_model: bool = False):
        """
        Overrides the predict_log_proba()-method from sklearn.ensemble.RandomForestClassifier
        in order to adapt it for the federation setting. Enables the prediction using the
        optimized federated silo-specific local model when use_updated_federated_model is set to True.

        Predict class log-probabilities for X.

        The predicted class log-probabilities of an input sample is computed as
        the log of the mean predicted class probabilities of the trees in the
        forest.

        Parameters
        ----------
        X: {array-like, sparse matrix} of shape (n_samples, n_features)
            The input samples. Internally, its dtype will be converted to
            ``dtype=np.float32``. If a sparse matrix is provided, it will be
            converted into a sparse ``csr_matrix``.

        Returns
        -------
        p: ndarray of shape (n_samples, n_classes), or a list of such arrays
            The class probabilities of the input samples. The order of the
            classes corresponds to that in the attribute :term:`classes_`.
        """
        # Setting this class variable is needed to prevent the model from changing self.estimators_
        # again when super().predict() calls predict_proba()
        self.predict_proba_called_by_outside_function = True
        # Set correct model for prediction
        if self.force_use_updated_tree:
            use_updated_federated_model = True

        self.estimators_ = helper.select_correct_model_for_prediction(
            self, use_updated_federated_model
        )
        preds = super().predict_log_proba(X)
        self.predict_proba_called_by_outside_function = False
        return preds

    def commit_local_random_forest(self) -> None:
        """
        This method transforms and transfers the local model's trees to the federated model. It further updates
        the feature mapping dictionary at the federated site. If the local model has been committed previously,
        the old trees will be replaced by the new ones at the federated site.
        """
        if self.model_is_trained:
            copy_of_local_trees = deepcopy(self.get_trees())
            # Update the federated model
            self.federated_random_forest.update_federated_model(
                copy_of_local_trees, self.local_feature_mapping, self.has_committed
            )
            # If the site commits the first time to the federated model set has_committed to True,
            # so that the next time the trees for this site will be replaced
            if not self.has_committed:
                self.has_committed = True

        else:
            raise RuntimeError(
                f"Trees can only be committed to the federated model, when "
                f"the model has been trained before. \n "
                f"Use LocalRandomForestClassifier.fit() to train the model locally."
            )

        return None

    def get_trees(self) -> list[DecisionTreeClassifier]:
        """
        Returns a list of decision trees that are part of the local model. The trees are
        provided in terms of the local column IDs. If no trees are available, the method
        returns an empty list.

        Returns
        -------
        list[DecisionTreeClassifier]
            A list of decision trees from the local model, using local column IDs. Returns a deep copy
            of the trees to ensure that the original data remains unmodified.
        """
        if hasattr(self, "estimators_"):
            trees = self.estimators_
        else:
            trees = None
        return deepcopy(trees)

    def get_local_feature_mapping(self) -> dict:
        """
        Returns the feature mapping dictionary of the local model. The feature mapping
        dictionary is used to map the local feature IDs to the global feature IDs in the
        federated model.

        Returns
        -------
        dict
            A dictionary containing the feature mapping of the local model. Returns a deep copy
            of the feature mapping to ensure that the original data remains unmodified.
        """
        return deepcopy(self.local_feature_mapping)

    def get_updated_trees_from_federated_model(self, commit_state: bool = False) -> list[DecisionTreeClassifier]:
        """
        Updates the local model with decision trees from the federated model. It only allows
        updates if the local model has previously committed to the federated model. The retrieved
        trees are adjusted to match the local feature mapping.

        Returns
        -------
        list[DecisionTreeClassifier]
            A list of updated decision trees from the federated model, tailored to the local feature mapping.
            The method returns a deep copy of the updated trees to ensure the integrity of the original data.


        """
        if commit_state:
            self.has_committed = commit_state
        # Only allows update, when local model has committed before
        if self.has_committed:
            number_local_trees = len(self.get_trees())
            self.updated_estimators_ = (
                self.federated_random_forest.get_trees_for_updating_local_model(
                    number_of_local_trees=number_local_trees,
                    local_feature_mapping=self.local_feature_mapping,
                    random_state=self.random_state,
                )
            )
        else:
            raise RuntimeError(
                f"Updated model can only be received from the federated model, "
                f"when the model has committed before. \n "
                f"Use LocalRandomForestClassifier.commit_local_random_forest() "
                f"to do that in advance."
            )
        return deepcopy(self.updated_estimators_)

    def get_local_trees(self) -> list[DecisionTreeClassifier]:
        """
        Returns the local trees of the model. The trees are returned in the form of a list of decision trees
        that are part of the local model. If no trees are available, the method returns an empty list.

        Returns
        -------
        list[BaseDecisionTree]
            A list of decision trees from the local model. Returns a deep copy
            of the trees to ensure that the original data remains unmodified.
        """
        try:
            self.local_estimators_ = deepcopy(self.estimators_)
        except AttributeError:
            self.local_estimators_ = None
        return self.local_estimators_

    def save_model(self, file_name: str = None, save_location_path: str = None, drop_fed: bool = False) -> None:
        """
        Saves the current instance of the LocalRandomForestClassifier model to a pickled file.

        Parameters
        ----------
        save_location_path: str, optional
            The path to the directory where the file will be saved. If None, the model is saved in the default
            sub-folder "local_rf_files" within the current working directory.
        """
        if not file_name:
            file_name = save_location_path.split("/")[-1]
            save_location_path = save_location_path.replace(file_name, "")

        if ".pkl" in file_name:
            file_name = file_name.replace(".pkl", "")

        # Validate critical attributes before saving
        critical_attrs = ['estimators_', 'local_feature_mapping', 'has_committed']
        missing_attrs = [attr for attr in critical_attrs if not hasattr(self, attr)]

        if missing_attrs:
            raise ValueError(f"Cannot save model: Missing critical attributes: {missing_attrs}")

        if drop_fed:
            # set federated_random_forest to None to avoid serialization issues
            self.federated_random_forest = None

        serializer.save_object(self,
                               default_save_folder_name="local_rf_files",
                               save_location_path=save_location_path,
                               file_name=file_name)

    @classmethod
    def load_model(cls, file_path: str, site_id: str = None) -> 'LocalRandomForestClassifier':
        """
        Loads an instance of the LocalRandomForestClassifier model from a pickled file.

        Parameters
        ----------
        file_path: str
            The path to the file containing the serialized LocalRandomForestClassifier model data.
        site_id: str, optional
            The site ID of the local model. If None, the site ID is loaded from the serialized model.
        Returns
        -------
        object
            An instance of the LocalRandomForestClassifier class, loaded from the specified file.
        """
        if site_id:
            cls.site_id = site_id

        model = serializer.load_object(cls, file_path)

        # Validate critical attributes after loading
        critical_attrs = ['estimators_', 'local_feature_mapping', 'has_committed']
        missing_attrs = [attr for attr in critical_attrs if not hasattr(model, attr)]

        if missing_attrs:
            raise ValueError(f"Model loading incomplete: Missing critical attributes: {missing_attrs}")

        return model
