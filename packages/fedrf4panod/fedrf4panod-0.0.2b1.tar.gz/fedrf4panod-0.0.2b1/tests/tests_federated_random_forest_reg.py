import os
import unittest

import helper as test_helper
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from fedrf4panod.federated_random_forest_regressor.federated_random_forest_reg import (
    FederatedRandomForestRegressor,
)
from fedrf4panod.federated_random_forest_regressor.local_random_forest_reg import (
    LocalRandomForestRegressor,
)


class TestFederatedRandomForest(unittest.TestCase):
    def test_blank_initialization(self):
        with self.assertRaises(TypeError):
            fed_rf = FederatedRandomForestRegressor()

    def test_initialization_unknown_aggregation_method(self):
        with self.assertRaises(TypeError):
            fed_rf = FederatedRandomForestRegressor(
                tree_aggregation_method="wrong_value", n_estimators=100
            )

    def test_initialization_unknown_sk_learn_parameters(self):
        with self.assertRaises(TypeError):
            fed_rf = FederatedRandomForestRegressor(
                tree_aggregation_method="add", n_estimators=100, unknown_sk_var_name=100
            )

    def test_initialization_of_wrong_weighting_parameter(self):
        with self.assertRaises(TypeError):
            fed_rf = FederatedRandomForestRegressor(
                tree_aggregation_method="add", weighting="unknown method"
            )

    def test_initialization_of_missing_rate_parameter(self):
        with self.assertRaises(ValueError):
            fed_rf = FederatedRandomForestRegressor(
                tree_aggregation_method="add", weighting="trees-per-sample-size-rate"
            )

    def test_correct_initialization_of_weighting_parameter(self):
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add",
            weighting="trees-per-sample-size-rate",
            trees_per_sample_size_rate=0.5,
        )

    def test_initializing_sk_learn_params_with_missing_weight_parameter(self):
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add", n_estimators=100
        )
        self.assertEqual(fed_rf.n_estimators, 100)

    def test_random_state_initialization(self):
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add", random_state=42
        )
        self.assertEqual(fed_rf.random_state, 42)

    def test_no_random_state_initialization(self):
        fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
        self.assertEqual(fed_rf.random_state, None)

    def test_initialization_with_sk_learn_parameters(self):
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add", n_estimators=100, max_features="log2"
        )
        self.assertEqual(fed_rf.tree_aggregation_method, "add")
        self.assertEqual(fed_rf.n_estimators, 100)
        self.assertEqual(fed_rf.max_features, "log2")
        self.assertEqual(fed_rf.federated_feature_mapping_dict, {})


class TestUpdateOfFederatedDictionary(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_regression.csv")
        # Drop the columns 's1' to 's6'
        self.data = self.data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        self.y = self.data["target"]
        # Get different dataset columns
        self.X = self.data.drop("target", axis=1)
        # X_1 has only the two columns 'age' and 'bmi'
        self.X_1 = self.data.drop(["target", "sex", "bp"], axis=1)
        # X_2 has the three columns 'age', 'bmi' and 'bp'
        self.X_2 = self.data.drop(["target", "sex"], axis=1)
        # Initialize & fit two local random forest on different subsets of the data
        self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
        local_rf_all = LocalRandomForestRegressor(self.fed_rf)
        local_rf_all.fit(self.X, self.y)
        self.local_dict_all = local_rf_all.local_feature_mapping
        local_rf_1 = LocalRandomForestRegressor(self.fed_rf)
        local_rf_1.fit(self.X_1, self.y)
        self.local_dict_1 = local_rf_1.local_feature_mapping
        local_rf_2 = LocalRandomForestRegressor(self.fed_rf)
        local_rf_2.fit(self.X_2, self.y)
        self.local_dict_2 = local_rf_2.local_feature_mapping

    def test_initialization_of_dictionary(self):
        # Reset dictionary
        self.fed_rf.federated_feature_mapping_dict = {}
        initialized_dict = self.fed_rf.update_federated_dictionary(self.local_dict_1)
        expected_dict = {
            "age": 0,
            "bmi": 1,
        }
        self.assertEqual(initialized_dict, expected_dict)
        # Update should work during function call implicitly
        self.assertEqual(self.fed_rf.federated_feature_mapping_dict, expected_dict)

    def test_update_of_dictionary_partly_duplicate_columns(self):
        # Reset dictionary
        self.fed_rf.federated_feature_mapping_dict = {}
        # Adds first two entries
        initialized_dict = self.fed_rf.update_federated_dictionary(self.local_dict_1)
        # Adds second two entries
        updated_dict = self.fed_rf.update_federated_dictionary(self.local_dict_all)
        expected_dict = {
            "age": 0,
            "bmi": 1,
            "sex": 2,
            "bp": 3,
        }
        self.assertEqual(updated_dict, expected_dict)
        # Update should work during function call implicitly
        self.assertEqual(self.fed_rf.federated_feature_mapping_dict, expected_dict)
        # Should be different encoding due to order of columns in local_dict_all
        self.assertNotEqual(updated_dict, self.local_dict_all)

    def test_update_of_dictionary_only_duplicate_columns(self):
        self.fed_rf.federated_feature_mapping_dict = {}
        # Adds first two entries
        initialized_dict = self.fed_rf.update_federated_dictionary(self.local_dict_1)
        # Adds last two entries
        updated_dict = self.fed_rf.update_federated_dictionary(self.local_dict_all)
        # Shouldn't add anything
        updated_dict = self.fed_rf.update_federated_dictionary(self.local_dict_2)
        expected_dict = {
            "age": 0,
            "bmi": 1,
            "sex": 2,
            "bp": 3,
        }
        self.assertEqual(updated_dict, expected_dict)
        # Update should work during function call implicitly
        self.assertEqual(self.fed_rf.federated_feature_mapping_dict, expected_dict)
        # Should be different encoding due to order of columns in local_dict_all
        self.assertNotEqual(updated_dict, self.local_dict_all)


class TestGetFeatureMapping(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_regression.csv")
        self.data = self.data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        self.y = self.data["target"]
        # Drop some columns, only 'age' and 'bmi' remain
        self.X = self.data.drop(["target", "sex", "bp"], axis=1)
        # Initialize & fit local random forest model
        self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
        local_rf = LocalRandomForestRegressor(self.fed_rf)
        local_rf.fit(self.X, self.y)
        self.local_dict = local_rf.local_feature_mapping

    def test_return_of_dictionary(self):
        # Check before initialization of dictionary
        self.assertEqual(self.fed_rf.federated_feature_mapping_dict, {})
        self.assertEqual(self.fed_rf.get_feature_mapping(), {})
        # Initialize federated dictionary
        initialized_dict = self.fed_rf.update_federated_dictionary(self.local_dict)
        expected_dict = {
            "age": 0,
            "bmi": 1,
        }
        # Check if the method works and gives us expected results
        self.assertEqual(self.fed_rf.federated_feature_mapping_dict, expected_dict)
        self.assertEqual(self.fed_rf.get_feature_mapping(), expected_dict)
        self.assertEqual(self.fed_rf.get_feature_mapping(), initialized_dict)


class TestUpdateOfFederatedModel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_regression.csv")
        data = data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        y = data["target"]
        # Drop some columns
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        self.fed_rf = FederatedRandomForestRegressor("add")
        # Initialize & fit local random forest model
        self.lrf_1 = LocalRandomForestRegressor(self.fed_rf)
        self.lrf_2 = LocalRandomForestRegressor(self.fed_rf)
        self.lrf_1.fit(X, y)
        self.lrf_2.fit(X, y)

    def test_initializing_and_update_of_federated_model(self):
        self.assertEqual(hasattr(self.fed_rf, "estimators_"), False)
        updated_federated_random_forest = self.fed_rf.update_federated_model(
            self.lrf_1.estimators_,
            self.lrf_1.local_feature_mapping,
            local_model_has_committed=False,
        )
        self.assertEqual(len(self.fed_rf.estimators_), len(self.lrf_1.estimators_))
        updated_federated_random_forest_2 = self.fed_rf.update_federated_model(
            self.lrf_2.estimators_,
            self.lrf_2.local_feature_mapping,
            local_model_has_committed=False,
        )
        trees_rf_1_and_2 = [*self.lrf_1.estimators_, *self.lrf_2.estimators_]
        self.assertEqual(len(self.fed_rf.estimators_), len(trees_rf_1_and_2))


class TestFederatedRandomForestGetTrees(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_regression.csv")
        self.data = self.data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        self.y = self.data["target"]
        self.X = self.data.drop("target", axis=1)
        # Train RandomForestRegressor with same random state on same dataset
        self.rf = RandomForestRegressor(random_state=42)
        self.rf.fit(self.X, self.y)

    def test_empty_return(self):
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add", random_state=42
        )
        federated_trees = fed_rf.get_trees()
        self.assertEqual(federated_trees, None)

    def test_compare_to_normal_rf(self):
        # Initialize federated & local model & commit trees
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="add", random_state=42
        )
        # Initialize & train local model
        local_rf = LocalRandomForestRegressor(fed_rf)
        local_rf.fit(self.X, self.y)
        local_rf.commit_local_random_forest()
        federated_trees = fed_rf.get_trees()
        # Compare to trees from RandomForestRegressor
        rf_trees = self.rf.estimators_
        test_helper.compare_trees(self, rf_trees, federated_trees)


class TestSaveModel(unittest.TestCase):

    def test_if_file_has_been_created(self):
        # Initialize federated model
        fed_rf = FederatedRandomForestRegressor(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        # Save the model
        filename = "fed_rf1"
        fed_rf.save_model(filename)
        # Determine expected path of the file
        current_dir = os.getcwd()
        save_folder_path = os.path.join(current_dir, "federated_rf_files")
        file_name_with_extension = filename + ".pkl"
        expected_file_path = os.path.join(save_folder_path, file_name_with_extension)
        # Check if file has been created
        self.assertTrue(os.path.isfile(expected_file_path))
        # Clean
        os.remove(expected_file_path)
        os.rmdir(save_folder_path)


class TestLoadModel(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_regression.csv")
        data = data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        self.fed_rf_1 = FederatedRandomForestRegressor(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        self.local_rf_1 = LocalRandomForestRegressor(self.fed_rf_1)
        # Train the model
        self.local_rf_1.fit(X, y)
        # Commit model to federated model
        self.local_rf_1.commit_local_random_forest()
        # Save federated model
        self.file_name = "fed_rf1"
        self.fed_rf_1.save_model(self.file_name)
        # Determine saving path
        self.current_dir = os.getcwd()
        self.save_folder_path = os.path.join(self.current_dir, "federated_rf_files")
        self.file_name_with_extension = self.file_name + ".pkl"
        self.expected_file_path = os.path.join(
            self.save_folder_path, self.file_name_with_extension
        )
        # Retrieve trees for later comparison
        self.fed_trees_1 = self.fed_rf_1.get_trees()
        # Save the local model too for checkign type compliance
        self.file_name_local_model = "local_rf1"
        self.local_rf_1.save_model(self.file_name_local_model)
        # Determine saving path for local model
        self.file_name_local_model_with_extension = self.file_name_local_model + ".pkl"
        self.save_folder_path_local_model = os.path.join(
            self.current_dir, "local_rf_files"
        )
        self.expected_file_path_local_model = os.path.join(
            self.save_folder_path_local_model, self.file_name_local_model_with_extension
        )

    def test_correct_loading_of_attributes(self):
        loaded_fed_rf = FederatedRandomForestRegressor.load_model(
            self.expected_file_path
        )
        self.assertEqual(loaded_fed_rf.n_estimators, self.fed_rf_1.n_estimators)
        self.assertEqual(loaded_fed_rf.random_state, self.fed_rf_1.random_state)
        self.assertEqual(loaded_fed_rf.max_depth, self.fed_rf_1.max_depth)
        self.assertEqual(
            loaded_fed_rf.tree_aggregation_method, self.fed_rf_1.tree_aggregation_method
        )

    def test_correct_loading_of_trees(self):
        loaded_fed_rf = FederatedRandomForestRegressor.load_model(
            self.expected_file_path
        )
        # Get the trees of the loaded model
        loaded_trees = loaded_fed_rf.get_trees()
        # Compare loaded trees from teh saved model with the previously derived federated model
        test_helper.compare_trees(self, loaded_trees, self.fed_trees_1)

    def test_error_when_loading_local_model(self):
        with self.assertRaises(TypeError):
            fed = FederatedRandomForestRegressor.load_model(
                self.expected_file_path_local_model
            )

    @classmethod
    def tearDownClass(self):
        os.remove(self.expected_file_path)
        os.remove(self.expected_file_path_local_model)
        os.rmdir(self.save_folder_path)
        os.rmdir(self.save_folder_path_local_model)


class TestPredict(unittest.TestCase):

    def setUp(self):
        self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="constant")
        # Load the data
        data = pd.read_csv("test_data/test_data_regression.csv")
        data = data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        self.y = data["target"]
        self.X = data.drop(["target"], axis=1)

    def test_error_when_calling_predict(self):
        with self.assertRaises(NotImplementedError):
            self.fed_rf.predict(self.X)


class TestFit(unittest.TestCase):

    def setUp(self):
        self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="constant")
        # Load the data
        data = pd.read_csv("test_data/test_data_regression.csv")
        data = data.drop(["s1", "s2", "s3", "s4", "s5", "s6"], axis=1)
        self.y = data["target"]
        self.X = data.drop(["target"], axis=1)

    def test_error_when_calling_fit(self):
        with self.assertRaises(NotImplementedError):
            self.fed_rf.fit(self.X, self.y)


if __name__ == "__main__":
    unittest.main()
