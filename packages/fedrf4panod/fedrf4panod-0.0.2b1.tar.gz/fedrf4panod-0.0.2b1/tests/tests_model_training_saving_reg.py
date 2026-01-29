import glob

import pandas as pd
import os
import unittest
from sklearn.model_selection import train_test_split
from fedrf4panod.federated_random_forest_regressor.federated_random_forest_reg import FederatedRandomForestRegressor
from fedrf4panod.federated_random_forest_regressor.local_random_forest_reg import LocalRandomForestRegressor


class TestFederatedRandomForest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        os.makedirs("test_outputs", exist_ok=True)
        cls.datasets = []
        cls.targets = []
        for i in range(1, 4):
            dataset = pd.read_csv(f"test_data/test_data_regression_location{i}.csv")
            cls.targets.append(dataset["target"])
            cls.datasets.append(dataset.drop(columns=["target"]))

    def setUp(self):
        """Initialize fresh models for each test"""
        self.fed_rf = None
        self.local_rf = None

    def test_1_local_training(self):
        """Test training and saving local models for all locations"""
        for idx in range(3):
            site_id = str(idx + 1)
            self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
            self.local_rf = LocalRandomForestRegressor(self.fed_rf, site_id=site_id)

            X_train, X_test, y_train, y_test = train_test_split(
                self.datasets[idx], self.targets[idx], test_size=0.2, random_state=42
            )

            self.local_rf.fit(X_train, y_train)
            save_path = f"test_outputs/local_rf{site_id}.pkl"
            self.local_rf.save_model(save_location_path=save_path)

            # Verify model is saved and can make predictions
            self.assertTrue(os.path.exists(save_path))
            y_pred = self.local_rf.predict(X_test)
            self.assertEqual(len(y_pred), len(y_test))

    def test_2_model_loading(self):
        """Test loading saved local models"""
        for idx in range(3):
            site_id = str(idx + 1)
            save_path = f"test_outputs/local_rf{site_id}.pkl"
            self.assertTrue(os.path.exists(save_path))

            self.fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
            self.local_rf = LocalRandomForestRegressor(self.fed_rf, site_id=site_id)

            loaded_rf = self.local_rf.load_model(save_path)
            self.assertIsInstance(loaded_rf, LocalRandomForestRegressor)
            self.assertEqual(loaded_rf.site_id, site_id)

            y_pred = loaded_rf.predict(self.datasets[idx])
            self.assertEqual(len(y_pred), len(self.targets[idx]))

    def test_3_model_aggregation(self):
        """Test aggregating local models into a federated model"""
        local_rfs = []
        fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
        local_rf = LocalRandomForestRegressor(fed_rf)

        # Load and collect all local models
        for i in range(1, 4):
            site_id = str(i)
            save_path = f"test_outputs/local_rf{site_id}.pkl"
            loaded_rf = local_rf.load_model(save_path, site_id=site_id)
            local_rfs.append(loaded_rf)

        # Aggregate models
        fed_rf = fed_rf.aggregate_local_models(local_rfs)

        # Save federated model
        save_path = "test_outputs/fed_rf_add.pkl"
        fed_rf.save_model(save_location_path=save_path)
        self.assertTrue(os.path.exists(save_path))

    def test_4_federated_predictions_add(self):
        """Test predictions using the aggregated federated model"""
        for idx in range(3):
            X_train, X_test, y_train, y_test = train_test_split(
                self.datasets[idx], self.targets[idx], test_size=0.2, random_state=42
            )

            fed_rf_path = "test_outputs/fed_rf_add.pkl"
            local_rf_path = f"test_outputs/local_rf{idx + 1}.pkl"

            self.assertTrue(os.path.exists(fed_rf_path))
            self.assertTrue(os.path.exists(local_rf_path))

            fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
            fed_rf = fed_rf.load_model(fed_rf_path)

            local_rf = LocalRandomForestRegressor(fed_rf)
            local_rf = local_rf.load_model(local_rf_path)

            # Compare predictions before and after federation
            local_preds = local_rf.predict(X_test, use_updated_federated_model=False)
            local_rf.commit_local_random_forest()
            local_rf.get_updated_trees_from_federated_model()
            fed_preds = local_rf.predict(X_test, use_updated_federated_model=True)

            self.assertEqual(len(local_preds), len(fed_preds))

    def test_5_model_aggregation_constant(self):
        """Test aggregating local models into a federated model"""
        local_rfs = []
        fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="add")
        local_rf = LocalRandomForestRegressor(fed_rf)

        # Load and collect all local models
        for i in range(1, 4):
            site_id = str(i)
            save_path = f"test_outputs/local_rf{site_id}.pkl"
            loaded_rf = local_rf.load_model(save_path, site_id=site_id)
            local_rfs.append(loaded_rf)

        # Aggregate models
        fed_rf = fed_rf.aggregate_local_models(local_rfs)

        # Save federated model
        save_path = "test_outputs/fed_rf_constant.pkl"
        fed_rf.save_model(save_location_path=save_path)
        self.assertTrue(os.path.exists(save_path))

    def test_6_federated_predictions_constant(self):
        """Test predictions using the aggregated federated model"""
        for idx in range(3):
            X_train, X_test, y_train, y_test = train_test_split(
                self.datasets[idx], self.targets[idx], test_size=0.2, random_state=42
            )

            fed_rf_path = "test_outputs/fed_rf_constant.pkl"
            local_rf_path = f"test_outputs/local_rf{idx + 1}.pkl"

            self.assertTrue(os.path.exists(fed_rf_path))
            self.assertTrue(os.path.exists(local_rf_path))

            fed_rf = FederatedRandomForestRegressor(tree_aggregation_method="constant")
            fed_rf = fed_rf.load_model(fed_rf_path)

            local_rf = LocalRandomForestRegressor(fed_rf)
            local_rf = local_rf.load_model(local_rf_path)

            # Compare predictions before and after federation
            local_preds = local_rf.predict(X_test, use_updated_federated_model=False)
            local_rf.commit_local_random_forest()
            local_rf.get_updated_trees_from_federated_model()
            fed_preds = local_rf.predict(X_test, use_updated_federated_model=True)

            self.assertEqual(len(local_preds), len(fed_preds))

    @classmethod
    def tearDownClass(cls):
        """Clean up all test files after all tests are complete"""
        # Remove all files in test_outputs directory
        for file_path in glob.glob("test_outputs/*.pkl"):
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

        # Remove the test_outputs directory
        try:
            os.rmdir("test_outputs")
            print("Removed test_outputs directory")
        except Exception as e:
            print(f"Error removing test_outputs directory: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)