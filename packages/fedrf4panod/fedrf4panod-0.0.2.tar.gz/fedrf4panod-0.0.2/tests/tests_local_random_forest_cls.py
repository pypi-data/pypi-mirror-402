import os
import unittest
import warnings

import helper as test_helper
import numpy as np
import pandas as pd
from parameterized import parameterized
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from fedrf4panod import local_random_forest_helper as helper
from fedrf4panod.federated_random_forest_classifier.federated_random_forest_cls import (
    FederatedRandomForestClassifier,
)
from fedrf4panod.federated_random_forest_classifier.local_random_forest_cls import (
    LocalRandomForestClassifier,
)


class TestLocalRandomForestInit(unittest.TestCase):
    def test_blank_initialization(self):
        with self.assertRaises(TypeError):
            local_rf = LocalRandomForestClassifier()

    def test_initialization_with_normal_RF(self):
        with self.assertRaises(TypeError):
            normal_rf = RandomForestClassifier()
            local_rf = LocalRandomForestClassifier(normal_rf)

    def test_correct_initialization(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            n_estimators=100,
            max_features="log2",
            weighting="trees-per-sample-size-rate",
            trees_per_sample_size_rate=0.5,
        )
        local_rf = LocalRandomForestClassifier(fed_rf)
        expected_param_dict = {"n_estimators": 100, "max_features": "log2"}
        self.assertEqual(local_rf.tree_aggregation_method, "constant")
        self.assertEqual(local_rf.n_estimators, 100)
        self.assertEqual(local_rf.max_features, "log2")
        self.assertEqual(local_rf.model_is_trained, False)
        self.assertEqual(local_rf.federated_random_forest, fed_rf)
        # check if the parameters are set correctly and present in the local model
        self.assertEqual(local_rf.n_estimators, expected_param_dict["n_estimators"])
        self.assertEqual(local_rf.max_features, expected_param_dict["max_features"])
        self.assertEqual(local_rf.weighting, "trees-per-sample-size-rate")
        self.assertEqual(local_rf.trees_per_sample_size_rate, 0.5)

    def test_random_state_initialization(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        local_rf = LocalRandomForestClassifier(fed_rf)
        self.assertEqual(local_rf.random_state, 42)

    def test_no_random_state_initialization(self):
        fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add")
        local_rf = LocalRandomForestClassifier(fed_rf)
        self.assertEqual(local_rf.random_state, None)

    def test_different_ids_between_different_sites(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        site_id_1 = local_rf_1.site_id
        site_id_2 = local_rf_2.site_id
        self.assertNotEqual(site_id_1, site_id_2)


class TestLocalRandomForestTraining(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"]
        self.X = self.data.drop("target", axis=1)
        self.fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", n_estimators=100, max_features="log2"
        )

    def test_data_not_in_dataframe_format(self):
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        X_np_array = self.X.to_numpy()
        with self.assertRaises(TypeError):
            local_rf.fit(X_np_array, self.y)

    def test_feature_mapping_created(self):
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        local_rf.fit(self.X, self.y)
        keys = local_rf.local_feature_mapping.keys()
        columns = self.X.columns
        for col in columns:
            self.assertIn(col, keys)

    def test_model_is_trained(self):
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        self.assertEqual(local_rf.model_is_trained, False)
        local_rf.fit(self.X, self.y)
        self.assertEqual(local_rf.model_is_trained, True)

    def test_trained_with_given_parameters(self):
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        local_rf.fit(self.X, self.y)
        self.assertEqual(local_rf.estimators_[0].max_features, "log2")
        self.assertEqual(len(local_rf.estimators_), 100)


class TestLocalRandomForestGetTrees(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"]
        self.X = self.data.drop("target", axis=1)
        self.fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train RandomForestClassifier with same random state on same dataset
        self.rf = RandomForestClassifier(random_state=42)
        self.rf.fit(self.X, self.y)

    def test_empty_return(self):
        # Initialize model
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        local_rf_trees = local_rf.get_trees()
        self.assertEqual(local_rf_trees, None)

    def test_compare_to_normal_rf(self):
        # Initialize & train local model
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        local_rf = LocalRandomForestClassifier(self.fed_rf)
        local_rf.fit(self.X, self.y)
        local_rf_trees = local_rf.get_trees()
        # Compare to RandomForestClassifier
        test_helper.compare_trees(self, local_rf_trees, self.rf.estimators_)


class TestCommitLocalRandomForest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"]
        self.X = self.data.drop("target", axis=1)

    def test_commit_before_training(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        with self.assertRaises(RuntimeError):
            local_rf = LocalRandomForestClassifier(fed_rf)
            local_rf.commit_local_random_forest()

    def test_commit_after_training(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        local_rf = LocalRandomForestClassifier(fed_rf)
        local_rf.fit(self.X, self.y)
        local_rf.commit_local_random_forest()
        self.assertEqual(len(fed_rf.estimators_), len(local_rf.estimators_))

    def test_replacement_after_second_commit(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train one local random forest model
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X, self.y)
        local_rf_1.commit_local_random_forest()
        # Train local model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X, self.y)
        # Annotate trees with old_tree attribute
        for tree in local_rf_2.estimators_:
            tree.is_old_tree = True
        # Commit local model
        local_rf_2.commit_local_random_forest()
        # Check if trees in federated model have the attribute
        for tree in fed_rf.estimators_:
            if hasattr(tree, "is_old_tree"):
                self.assertTrue(tree.is_old_tree)
        # Re-train local model
        local_rf_2.fit(self.X, self.y)
        # Check that the attribute is not there anymore and we have new trees after re-training
        for tree in local_rf_2.estimators_:
            self.assertFalse(hasattr(tree, "is_old_tree"))
            # And set is_old_tree to false afterwards
            tree.is_old_tree = False
        # Commit new trees to the federated model
        local_rf_2.commit_local_random_forest()
        # Check if all(!) trees in the federated now are new trees
        for tree in fed_rf.estimators_:
            if hasattr(tree, "is_old_tree"):
                self.assertFalse(tree.is_old_tree)


class TestGetUpdatedTreesFromFederatedModel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"]
        self.X_1 = self.data.drop(["target", "petal length (cm)"], axis=1)
        self.X_2 = self.data.drop(["target", "sepal length (cm)"], axis=1)

    def test_if_call_fails_when_model_has_not_committed(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, max_depth=2
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_1, self.y)
        local_rf_1.commit_local_random_forest()
        # Train and fit but NOT commit model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_2, self.y)
        with self.assertRaises(RuntimeError):
            local_rf_2.get_updated_trees_from_federated_model()

    def test_if_updated_estimators__is_set(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, max_depth=2
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_1, self.y)
        local_rf_1.commit_local_random_forest()
        # Train and fit but NOT commit model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_2, self.y)
        local_rf_2.commit_local_random_forest()
        self.assertEqual(hasattr(local_rf_2, "updated_estimators_"), False)
        local_rf_2.get_updated_trees_from_federated_model()
        self.assertEqual(hasattr(local_rf_2, "updated_estimators_"), True)

    def test_if_trees_got_added(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, max_depth=2
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_1, self.y)
        local_rf_1.commit_local_random_forest()
        # Train and fit but NOT commit model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_2, self.y)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        self.assertNotEqual(
            len(local_rf_2.updated_estimators_), len(local_rf_2.estimators_)
        )

    def test_constant_aggregation_of_trees(self):
        n = 50
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=n,
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_1, self.y)
        local_rf_1.commit_local_random_forest()
        # Train and fit but NOT commit model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_2, self.y)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        self.assertEqual(
            len(local_rf_2.updated_estimators_), len(local_rf_2.estimators_)
        )
        self.assertEqual(len(local_rf_2.updated_estimators_), 50)

    def test_check_constant_aggregation_reproducibility(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        X = self.data.drop(["target"], axis=1)
        y = self.data["target"]
        X_1, X_2, y_1, y_2 = train_test_split(X, y, test_size=0.5, random_state=42)
        # Create a federated random forest
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant", random_state=42, max_depth=2
        )
        # Create two local random forests on same dataset
        local_rf1 = LocalRandomForestClassifier(fed_rf)
        local_rf2 = LocalRandomForestClassifier(fed_rf)
        # Train models on the same dataset
        local_rf1.fit(X_1, y_1)
        local_rf2.fit(X_2, y_2)
        # Commit both models
        local_rf1.commit_local_random_forest()
        local_rf2.commit_local_random_forest()
        # Get the updated model
        updated_trees = local_rf1.get_updated_trees_from_federated_model()
        # Rerun this and save the value array
        fed_rf_rerun = FederatedRandomForestClassifier(
            tree_aggregation_method="constant", random_state=42, max_depth=2
        )
        local_rf1_rerun = LocalRandomForestClassifier(fed_rf_rerun)
        local_rf2_rerun = LocalRandomForestClassifier(fed_rf_rerun)
        local_rf1_rerun.fit(X_1, y_1)
        local_rf2_rerun.fit(X_2, y_2)
        local_rf1_rerun.commit_local_random_forest()
        local_rf2_rerun.commit_local_random_forest()
        updated_trees_rerun = local_rf1_rerun.get_updated_trees_from_federated_model()
        # Compare the updated trees with the updated trees from the rerun, to check reproducibility
        test_helper.compare_trees(self, updated_trees, updated_trees_rerun)
        # Rerun this with a different random state
        fed_rf_rerun_diff_seed = FederatedRandomForestClassifier(
            tree_aggregation_method="constant", random_state=1, max_depth=2
        )
        local_rf1_rerun_diff_seed = LocalRandomForestClassifier(fed_rf_rerun_diff_seed)
        local_rf2_rerun_diff_seed = LocalRandomForestClassifier(fed_rf_rerun_diff_seed)
        local_rf1_rerun_diff_seed.fit(X_1, y_1)
        local_rf2_rerun_diff_seed.fit(X_2, y_2)
        local_rf1_rerun_diff_seed.commit_local_random_forest()
        local_rf2_rerun_diff_seed.commit_local_random_forest()
        updated_trees_rerun_diff_seed = (
            local_rf1_rerun_diff_seed.get_updated_trees_from_federated_model()
        )
        # Check that at least one tree from differ when using another seed
        test_helper.compare_trees(
            self,
            updated_trees[:1],
            updated_trees_rerun_diff_seed[:1],
            assertEqual=False,
        )


class TestPredictUseUpdatedModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        X_1 = self.data.drop(["target", "petal length (cm)"], axis=1)
        X_2 = self.data.drop(["target", "sepal length (cm)"], axis=1)
        # Do train-test split
        self.X_train_1, self.X_test_1, self.y_train_1, self.y_test_1 = train_test_split(
            X_1, y, test_size=0.2, random_state=42
        )
        # Do train-test split
        self.X_train_2, self.X_test_2, self.y_train_2, self.y_test_2 = train_test_split(
            X_2, y, test_size=0.2, random_state=42
        )

    def test_local_prediction(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        pred = local_rf_1.predict(self.X_test_1)
        # Due to random_state we can check if the prediction still gives same value
        self.assertEqual(pred[0], 1)
        self.assertEqual(pred[1], 0)
        self.assertEqual(pred[2], 2)

    def test_updated_prediction_updated_model_not_set(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        with self.assertRaises(RuntimeError):
            local_rf_1.predict(self.X_train_1, use_updated_federated_model=True)

    def test_updated_prediction_same_model(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        pred_before = local_rf_1.predict_proba(self.X_test_1)
        local_rf_1.commit_local_random_forest()
        local_rf_1.get_updated_trees_from_federated_model()
        pred_after = local_rf_1.predict_proba(
            self.X_test_1, use_updated_federated_model=True
        )
        self.assertEqual(pred_before[0][0], pred_after[0][0])
        self.assertEqual(pred_before[1][0], pred_after[1][0])
        self.assertEqual(pred_before[2][0], pred_after[2][0])
        self.assertEqual(pred_before[3][0], pred_after[3][0])
        self.assertEqual(pred_before[4][0], pred_after[4][0])

    def test_updated_prediction_new_model(self):
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, max_depth=2
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        pred_before = local_rf_2.predict_proba(self.X_test_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        pred_after = local_rf_2.predict_proba(
            self.X_test_2, use_updated_federated_model=True
        )
        self.assertNotEqual(pred_before[0][0], pred_after[0][0])
        self.assertNotEqual(pred_before[1][0], pred_after[1][0])
        self.assertNotEqual(pred_before[2][0], pred_after[2][0])
        self.assertNotEqual(pred_before[3][0], pred_after[3][0])
        self.assertNotEqual(pred_before[4][0], pred_after[4][0])

    @parameterized.expand(
        [
            (None, "add", None),
            (None, "constant", None),
            ("weighted-sampling", "constant", None),
            ("trees-per-sample-size-rate", "add", 1),
            ("trees-per-sample-size-rate", "constant", 1),
        ]
    )
    def test_no_error_during_prediction_using_different_parameters(
        self, weighting, aggregation, rate
    ):
        fed_rf = FederatedRandomForestClassifier(
            weighting=weighting,
            tree_aggregation_method=aggregation,
            trees_per_sample_size_rate=rate,
            random_state=42,
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        # Just see if no error occurs
        pred_proba_before = local_rf_2.predict_proba(self.X_test_2)
        pred_before = local_rf_2.predict(self.X_test_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        # Just see if no error occurs
        pred_proba_after = local_rf_2.predict_proba(
            self.X_test_2, use_updated_federated_model=True
        )
        pred_after = local_rf_2.predict(self.X_test_2, use_updated_federated_model=True)


class TestPredictProba(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        X_1 = self.data.drop(["target", "petal length (cm)"], axis=1)
        X_2 = self.data.drop(["target", "sepal length (cm)"], axis=1)
        # Do train-test split
        self.X_train_1, self.X_test_1, self.y_train_1, self.y_test_1 = train_test_split(
            X_1, y, test_size=0.2, random_state=42
        )
        # Do train-test split
        self.X_train_2, self.X_test_2, self.y_train_2, self.y_test_2 = train_test_split(
            X_2, y, test_size=0.2, random_state=42
        )

    def test_validation_of_prediction_results_before_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        preds = local_rf_2.predict_proba(self.X_test_2)
        self.assertListEqual(preds[0].tolist(), [0.0, 0.95, 0.05])
        self.assertListEqual(preds[1].tolist(), [1.0, 0.0, 0.0])
        self.assertListEqual(preds[2].tolist(), [0.0, 0.01, 0.99])
        self.assertListEqual(preds[3].tolist(), [0.0, 1.0, 0.0])

    def test_validation_of_prediction_results_after_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        pred = local_rf_2.predict_proba(self.X_test_2, use_updated_federated_model=True)
        rounded_preds = np.round(pred, decimals=5)
        self.assertListEqual(rounded_preds[0].tolist(), [0.0, 0.95098, 0.04902])
        self.assertListEqual(rounded_preds[1].tolist(), [1.0, 0.0, 0.0])
        self.assertListEqual(rounded_preds[2].tolist(), [0.0, 0.0098, 0.9902])
        self.assertListEqual(rounded_preds[3].tolist(), [0.0, 1.0, 0.0])


class TestPredictLogProba(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        X_1 = self.data.drop(["target", "petal length (cm)"], axis=1)
        X_2 = self.data.drop(["target", "sepal length (cm)"], axis=1)
        # Do train-test split
        self.X_train_1, self.X_test_1, self.y_train_1, self.y_test_1 = train_test_split(
            X_1, y, test_size=0.2, random_state=42
        )
        # Do train-test split
        self.X_train_2, self.X_test_2, self.y_train_2, self.y_test_2 = train_test_split(
            X_2, y, test_size=0.2, random_state=42
        )

    def test_validation_of_prediction_results_before_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        # Filter -inf warning
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=RuntimeWarning,
                message="divide by zero encountered in log",
            )
            pred = local_rf_2.predict_log_proba(self.X_test_2)
        rounded_preds = np.round(pred, decimals=5)
        self.assertListEqual(rounded_preds[0].tolist(), [-np.inf, -0.05129, -2.99573])
        self.assertListEqual(rounded_preds[1].tolist(), [0.0, -np.inf, -np.inf])
        self.assertListEqual(rounded_preds[2].tolist(), [-np.inf, -4.60517, -0.01005])
        self.assertListEqual(rounded_preds[3].tolist(), [-np.inf, 0.0, -np.inf])

    def test_validation_of_prediction_results_after_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        # Filter -inf warning
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=RuntimeWarning,
                message="divide by zero encountered in log",
            )
            pred = local_rf_2.predict_log_proba(
                self.X_test_2, use_updated_federated_model=True
            )
        rounded_preds = np.round(pred, decimals=5)
        self.assertListEqual(rounded_preds[0].tolist(), [-np.inf, -0.05026, -3.01553])
        self.assertListEqual(rounded_preds[1].tolist(), [0.0, -np.inf, -np.inf])
        self.assertListEqual(rounded_preds[2].tolist(), [-np.inf, -4.62497, -0.00985])
        self.assertListEqual(rounded_preds[3].tolist(), [-np.inf, 0.0, -np.inf])


class TestPredict(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        X_1 = self.data.drop(["target", "petal length (cm)"], axis=1)
        X_2 = self.data.drop(["target", "sepal length (cm)"], axis=1)
        # Do train-test split
        self.X_train_1, self.X_test_1, self.y_train_1, self.y_test_1 = train_test_split(
            X_1, y, test_size=0.2, random_state=42
        )
        # Do train-test split
        self.X_train_2, self.X_test_2, self.y_train_2, self.y_test_2 = train_test_split(
            X_2, y, test_size=0.2, random_state=42
        )

    def test_validation_of_prediction_results_before_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        pred = local_rf_2.predict(self.X_test_2)
        expected_preds_from_seed = [
            1,
            0,
            2,
            1,
            1,
            0,
            1,
            2,
            1,
            1,
            2,
            0,
            0,
            0,
            0,
            1,
            2,
            1,
            1,
            2,
            0,
            2,
            0,
            2,
            2,
            2,
            2,
            2,
            0,
            0,
        ]
        self.assertListEqual(pred.tolist(), expected_preds_from_seed)

    def test_validation_of_prediction_results_after_using_updated_model(self):
        # Set seed by using random state and compare fixed result to the predictions from the state before
        # overwriting predictions in order to verify their correctness
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_2, self.y_train_2)
        local_rf_2.commit_local_random_forest()
        local_rf_2.get_updated_trees_from_federated_model()
        pred = local_rf_2.predict(self.X_test_2, use_updated_federated_model=True)
        expected_preds_from_seed = [
            1,
            0,
            2,
            1,
            1,
            0,
            1,
            2,
            1,
            1,
            2,
            0,
            0,
            0,
            0,
            1,
            2,
            1,
            1,
            2,
            0,
            2,
            0,
            2,
            2,
            2,
            2,
            2,
            0,
            0,
        ]
        self.assertListEqual(pred.tolist(), expected_preds_from_seed)


class TestManualVerificationToyExample(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        y = self.data["target"]
        X_val1 = self.data[["sepal length (cm)", "sepal width (cm)"]]
        X_val2 = self.data[["petal length (cm)", "petal width (cm)"]]
        X_val3 = self.data.drop(["target"], axis=1)
        # Do train-test split
        self.X_train_val1, self.X_test_val1, self.y_train_val1, self.y_test_val1 = (
            train_test_split(X_val1, y, test_size=0.2, random_state=42)
        )
        self.X_train_val2, self.X_test_val2, self.y_train_val2, self.y_test_val2 = (
            train_test_split(X_val2, y, test_size=0.2, random_state=43)
        )
        self.X_train_val3, self.X_test_val3, self.y_train_val3, self.y_test_val3 = (
            train_test_split(X_val3, y, test_size=0.2, random_state=44)
        )
        # Manual dataset used to exactly check the thresholds of the trees and be sure which path they should take
        manual_test_data = {
            "sepal length (cm)": [50.0, 50.0, 50.0],
            "sepal width (cm)": [3.34, 3.36, 3.34],
            "petal length (cm)": [50.0, 50.0, 50.0],
            "petal width (cm)": [0.6, 1.7, 1.8],
        }
        self.X_manual_test_data = pd.DataFrame(manual_test_data)

    def test_manual_toy_example(self):
        # To enable manual checking and calculating the probabilities of the trees we limit the
        # depth & number of estimators to 1
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, max_depth=1, n_estimators=1
        )

        ###########################################
        #### Train local models & commit them #####
        ###########################################

        # Train & commit local model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_val1, self.y_train_val1)
        # Splits for sepal width with <= 3.35 -> 1  & > 3.35 -> 0
        tree_1_abs_class_distribution_values = local_rf_1.estimators_[
            0
        ].tree_.value  # Needed for verification of prediction later
        # We need to iterate through the values so that we can calculate the respective probabilities, since we
        # have 3 individual arrays stored here, one for each node in the tree
        tree_1_leaf_class_probabilities = []
        for abs_leaf_class_distribution in tree_1_abs_class_distribution_values:
            # Turn absolute values into class probabilities for every leaf
            tree_1_leaf_class_probabilities.append(
                abs_leaf_class_distribution[0] / abs_leaf_class_distribution[0].sum()
            )
        local_rf_1.commit_local_random_forest()
        # Train & commit local model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_train_val2, self.y_train_val2)
        tree_2_abs_class_distribution_values = local_rf_2.estimators_[
            0
        ].tree_.value  # Needed for verification of prediction later
        tree_2_leaf_class_probabilities = []
        for abs_leaf_class_distribution in tree_2_abs_class_distribution_values:
            # Turn absolute values into class probabilities for every leaf
            tree_2_leaf_class_probabilities.append(
                abs_leaf_class_distribution[0] / abs_leaf_class_distribution[0].sum()
            )
        # Splits for petal width with <=1.75 -> 0  & >1.75 -> 2
        local_rf_2.commit_local_random_forest()
        # Train & commit local model 3
        local_rf_3 = LocalRandomForestClassifier(fed_rf)
        local_rf_3.fit(self.X_train_val3, self.y_train_val3)
        tree_3_abs_class_distribution_values = local_rf_3.estimators_[
            0
        ].tree_.value  # Needed for verification of prediction later
        tree_3_leaf_class_probabilities = []
        for i, abs_leaf_class_distribution in enumerate(
            tree_3_abs_class_distribution_values
        ):
            # Turn absolute values into class probabilities for every leaf
            tree_3_leaf_class_probabilities.append(
                abs_leaf_class_distribution[0] / abs_leaf_class_distribution[0].sum()
            )
        # Splits for petal width with <=0.7 -> 0  & >0.7 -> 1
        local_rf_3.commit_local_random_forest()

        ###########################################
        ######### Validate updated model ##########
        ###########################################

        # Validation
        # Model 3 should get every tree (3 in total)
        updated_model_3 = local_rf_3.get_updated_trees_from_federated_model()
        self.assertEqual(len(updated_model_3), 3)
        # Tree 1 should predict [1, 0, 1]
        # Tree 2 should predict [0, 0, 2]
        # Tree 3 should predict [0, 1, 1]
        # With the tree_.values arrays we can calculate the respective probabilities,
        # considering the tree path / leaf we will end at:
        mean_for_sample_1 = np.mean(
            np.stack(
                (
                    tree_1_leaf_class_probabilities[1],
                    tree_2_leaf_class_probabilities[1],
                    tree_3_leaf_class_probabilities[1],
                )
            ),
            axis=0,
        )
        mean_for_sample_2 = np.mean(
            np.stack(
                (
                    tree_1_leaf_class_probabilities[2],
                    tree_2_leaf_class_probabilities[1],
                    tree_3_leaf_class_probabilities[2],
                )
            ),
            axis=0,
        )
        mean_for_sample_3 = np.mean(
            np.stack(
                (
                    tree_1_leaf_class_probabilities[1],
                    tree_2_leaf_class_probabilities[2],
                    tree_3_leaf_class_probabilities[2],
                )
            ),
            axis=0,
        )
        # Aggregate the estimated predictions from the local models to compare it to the ones from the updated model
        estimated_prediction = []
        estimated_prediction.append(np.argmax(mean_for_sample_1))
        estimated_prediction.append(np.argmax(mean_for_sample_2))
        estimated_prediction.append(np.argmax(mean_for_sample_3))
        estimated_prediction_proba = []
        estimated_prediction_proba.append(mean_for_sample_1)
        estimated_prediction_proba.append(mean_for_sample_2)
        estimated_prediction_proba.append(mean_for_sample_3)
        prediction_model_3 = local_rf_3.predict(
            self.X_manual_test_data, use_updated_federated_model=True
        )
        prediction_prob_model_3 = local_rf_3.predict_proba(
            self.X_manual_test_data, use_updated_federated_model=True
        )
        # Validation works
        # Compare estimated predictions based on local models with the one from the global model
        self.assertEqual(estimated_prediction, prediction_model_3.tolist())
        self.assertEqual(
            estimated_prediction_proba[0].tolist(), prediction_prob_model_3[0].tolist()
        )
        self.assertEqual(
            estimated_prediction_proba[1].tolist(), prediction_prob_model_3[1].tolist()
        )
        self.assertEqual(
            estimated_prediction_proba[2].tolist(), prediction_prob_model_3[2].tolist()
        )

        ###########################################
        ### Validate switch back to local model ###
        ###########################################

        prediction_prob_local_model_3 = local_rf_3.predict_proba(
            self.X_manual_test_data
        )

        a = tree_3_leaf_class_probabilities[1]
        b = prediction_prob_local_model_3[0]
        # Compare the leaf (1 / 2) class probabilities according to the decision path with
        # the corresponding prediction of the model, should be the same as the ones from
        # earlier again (the leaf class probabilities of the local tree 3)
        self.assertEqual(
            tree_3_leaf_class_probabilities[1].tolist(),
            prediction_prob_local_model_3[0].tolist(),
        )
        self.assertEqual(
            tree_3_leaf_class_probabilities[2].tolist(),
            prediction_prob_local_model_3[1].tolist(),
        )
        self.assertEqual(
            tree_3_leaf_class_probabilities[2].tolist(),
            prediction_prob_local_model_3[2].tolist(),
        )

        ###########################################
        ##### Validate update of other trees ######
        ###########################################

        # Update the other local models
        updated_model_1 = local_rf_1.get_updated_trees_from_federated_model()
        updated_model_2 = local_rf_2.get_updated_trees_from_federated_model()

        # Local model 1 is expected to hae the same number of trees, since the other trees are
        # using variables unkown to the site

        # Local model 2 should get the tree only from local model 3, as it uses the same variable
        self.assertEqual(len(updated_model_1), 1)
        self.assertEqual(len(updated_model_2), 2)


class TestRateBasedWeightingApproach(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"]
        self.X = self.data.drop(["target"], axis=1)
        self.X_1, self.X_2, self.y_1, self.y_2 = train_test_split(
            self.X, self.y, test_size=0.3, random_state=42
        )
        self.X_1, self.X_1_small, self.y_1, self.y_1_small = train_test_split(
            self.X_1, self.y_1, test_size=0.05, random_state=42
        )
        self.X_1 = self.X_1.drop(["sepal length (cm)"], axis=1)
        self.X_1_small = self.X_1_small.drop(["sepal length (cm)"], axis=1)
        self.X_2 = self.X_2.drop(["sepal width (cm)"], axis=1)

    def test_check_if_rate_is_used_to_adjust_number_of_trees(self):
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
            weighting="trees-per-sample-size-rate",
            trees_per_sample_size_rate=0.5,
        )
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        # Before training, n_estimators should be 100 as initialized within federated model
        self.assertEqual(local_rf_1.n_estimators, 100)
        local_rf_1.fit(self.X_1, self.y_1)
        # Site-size should be equal to 99 based on random-state splitting
        self.assertEqual(local_rf_1.site_size, 99)
        # Based on the rate, after training n_estimators should be changed to 99*0.5 = 49.5, so 50 rounded
        self.assertEqual(local_rf_1.n_estimators, 50)
        # Number of trees should therefore be 50 as well
        self.assertEqual(len(local_rf_1.estimators_), 50)
        # Initialize model 2
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        # Before training, n_estimators should be 100 as initialized within federated model
        self.assertEqual(local_rf_2.n_estimators, 100)
        local_rf_2.fit(self.X_2, self.y_2)
        # Site-size should be equal to 45 based on random-state splitting
        self.assertEqual(local_rf_2.site_size, 45)
        # Based on the rate, after training n_estimators should be changed to 45*0.5 = 22.5, so 22 rounded (nearest even number)
        self.assertEqual(local_rf_2.n_estimators, 22)
        # Number of trees should therefore be 22 as well
        self.assertEqual(len(local_rf_2.estimators_), 22)

    def test_check_if_warning_will_be_printed_when_n_estimators_is_too_low(self):
        # Catch all the warnings in w
        with warnings.catch_warnings(record=True) as w:
            # Check the warning hasn't been triggered in the beginning
            self.assertEqual(len(w), 0)
            # Initialize federated model
            fed_rf = FederatedRandomForestClassifier(
                tree_aggregation_method="constant",
                random_state=42,
                max_depth=2,
                n_estimators=100,
                weighting="trees-per-sample-size-rate",
                trees_per_sample_size_rate=0.5,
            )
            local_rf_1 = LocalRandomForestClassifier(fed_rf)
            local_rf_1.fit(self.X_1_small, self.y_1_small)
            # Check the warning has been triggered due to small dataset
            self.assertEqual(len(w), 1)
            local_rf_2 = LocalRandomForestClassifier(fed_rf)
            local_rf_2.fit(self.X_2, self.y_2)
            # Check that no further warning has been triggered
            self.assertEqual(len(w), 1)

    def test_check_committing_and_getting_updates(self):
        # Create federated model
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
            weighting="trees-per-sample-size-rate",
            trees_per_sample_size_rate=1,
        )
        # Train and commit local models with different site size
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_1, self.y_1)
        local_rf_1.commit_local_random_forest()
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        local_rf_2.fit(self.X_2, self.y_2)
        local_rf_2.commit_local_random_forest()
        # Check that global model consist of weighted number of all sites
        local_size_1 = local_rf_1.site_size
        local_number_of_trees_1 = len(local_rf_1.estimators_)
        local_size_2 = local_rf_2.site_size
        local_number_of_trees_2 = len(local_rf_2.estimators_)
        sample_sizes = local_size_1 + local_size_2
        self.assertEqual(local_size_1, local_number_of_trees_1)  # Same, since rate is 1
        self.assertEqual(local_size_2, local_number_of_trees_2)  # Same, since rate is 1
        self.assertEqual(len(fed_rf.estimators_), sample_sizes)
        # Save the local model for later comparison
        local_trees_1 = local_rf_1.get_trees()
        # Get updated for the local model 1
        local_trees_1_updated = local_rf_1.get_updated_trees_from_federated_model()
        # Check that the local model 1 receives trees from the global model (models are not equal)
        # Get the model values for the local model
        values_local_model = []
        for decision_tree in local_trees_1:
            values_local_model.append(decision_tree.tree_.value)
        # Get the model values for the updated model
        values_updated_model = []
        for decision_tree in local_trees_1_updated:
            values_updated_model.append(decision_tree.tree_.value)
        # Compare first entry of value arrays, should be different
        self.assertFalse(
            np.array_equal(
                values_local_model[0], values_updated_model[0], equal_nan=True
            )
        )

class TestLoadModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        self.local_rf_1 = LocalRandomForestClassifier(fed_rf)
        # Train the model
        self.local_rf_1.fit(X, y)
        file_name = "local_rf1"
        self.local_rf_1.save_model(file_name)
        # Determine saving path
        self.current_dir = os.getcwd()
        self.file_name_with_extension = file_name + ".pkl"
        self.save_folder_path = os.path.join(self.current_dir, "local_rf_files")
        self.expected_file_path = os.path.join(
            self.save_folder_path, self.file_name_with_extension
        )
        # Save the trees of the local model for later comparison
        self.local_trees_1 = self.local_rf_1.get_trees()
        # Save federated model to check type-compliance
        fed_rf.save_model(file_name)
        self.save_federated_folder_path = os.path.join(
            self.current_dir, "federated_rf_files"
        )
        self.path_federated_file = os.path.join(
            self.save_federated_folder_path, self.file_name_with_extension
        )

    def test_correct_loading_of_attributes(self):
        loaded_rf = LocalRandomForestClassifier.load_model(self.expected_file_path)
        self.assertEqual(loaded_rf.n_estimators, self.local_rf_1.n_estimators)
        self.assertEqual(loaded_rf.random_state, self.local_rf_1.random_state)
        self.assertEqual(loaded_rf.max_depth, self.local_rf_1.max_depth)
        self.assertEqual(
            loaded_rf.tree_aggregation_method, self.local_rf_1.tree_aggregation_method
        )

    def test_correct_loading_of_trees(self):
        loaded_rf = LocalRandomForestClassifier.load_model(self.expected_file_path)
        # Get the trees of the loaded model
        loaded_trees = loaded_rf.get_trees()
        # Compare the loaded trees with the previously trained local model
        test_helper.compare_trees(self, loaded_trees, self.local_trees_1)

    def test_error_when_loading_federated_model(self):
        with self.assertRaises(TypeError):
            fed = LocalRandomForestClassifier.load_model(self.path_federated_file)

    @classmethod
    def tearDownClass(self):
        os.remove(self.expected_file_path)
        os.remove(self.path_federated_file)
        os.rmdir(self.save_folder_path)
        os.rmdir(self.save_federated_folder_path)


class TestWeightedSampling(unittest.TestCase):

    @classmethod
    def setUp(self):
        rs = 42
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        self.X_site_1, self.X_site_2, self.y_site_1, self.y_site_2 = train_test_split(
            X, y, test_size=0.2, random_state=rs
        )
        # Initialize federated model
        self.fed_rf = FederatedRandomForestClassifier(
            weighting="weighted-sampling",
            tree_aggregation_method="constant",
            random_state=rs,
            max_depth=2,
            n_estimators=100,
        )
        self.local_rf_1 = LocalRandomForestClassifier(self.fed_rf)
        # Train the model 1
        self.local_rf_1.fit(self.X_site_1, self.y_site_1)
        # Annotate trees with site id that shouldn't be removed
        self.local_rf_1.estimators_ = helper.annotate_trees_with_attribute(
            trees=self.local_rf_1.estimators_,
            attribute_name="non_removable_site_id",
            attribute_value=1,
        )
        self.local_rf_2 = LocalRandomForestClassifier(self.fed_rf)
        # Train the model 2
        self.local_rf_2.fit(self.X_site_2, self.y_site_2)
        # Annotate trees with site id that shouldn't be removed
        self.local_rf_2.estimators_ = helper.annotate_trees_with_attribute(
            trees=self.local_rf_2.estimators_,
            attribute_name="non_removable_site_id",
            attribute_value=2,
        )
        # Commit to federated model
        self.local_rf_1.commit_local_random_forest()
        self.local_rf_2.commit_local_random_forest()
        # Get updated models
        self.local_rf_1.get_updated_trees_from_federated_model()
        self.local_rf_2.get_updated_trees_from_federated_model()

    def test_prediction_after_weighted_sampling(self):
        preds_before_update = self.local_rf_2.predict(self.X_site_1)
        preds_after_update = self.local_rf_2.predict(
            self.X_site_1, use_updated_federated_model=True
        )
        # Check that predictions change when incorporating updated model
        self.assertNotEqual(preds_before_update.tolist(), preds_after_update.tolist())

    def test_correct_sampling_rate_based_on_site_sizes(self):
        sampled_model_2 = self.local_rf_1.updated_estimators_
        counter_1 = 0
        counter_2 = 0
        # Count which tree belongs to which site
        for sampled_tree in sampled_model_2:
            if sampled_tree.non_removable_site_id == 1:
                counter_1 += 1
            if sampled_tree.non_removable_site_id == 2:
                counter_2 += 1
        # Check if 75 < counter 1 < 85
        self.assertGreater(counter_1, 75)
        self.assertGreater(85, counter_1)
        # Check if 15 < counter 2 < 25
        self.assertGreater(counter_2, 15)
        self.assertGreater(25, counter_2)

    def test_site_info_got_removed(self):
        # Check that attributes are present before removal
        example_tree_with_annotations = self.local_rf_1.local_estimators_[0]
        has_site_id = hasattr(example_tree_with_annotations, "site_id")
        has_site_size = hasattr(example_tree_with_annotations, "site_size")
        self.assertTrue(has_site_id)
        self.assertTrue(has_site_size)
        # Check that the site_id has been removed
        updated_trees = self.local_rf_1.updated_estimators_
        for tree in updated_trees:
            has_site_id = hasattr(tree, "site_id")
            has_site_size = hasattr(tree, "site_size")
            self.assertFalse(has_site_id)
            self.assertFalse(has_site_size)


if __name__ == "__main__":
    unittest.main()
