import glob
import unittest
import pandas as pd
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from fedrf4panod.federated_random_forest_classifier.federated_random_forest_cls import (
    FederatedRandomForestClassifier,
)
from fedrf4panod.federated_random_forest_classifier.local_random_forest_cls import (
    LocalRandomForestClassifier,
)


class FedRFTestBase(unittest.TestCase):
    """Base test class with common setup and utility methods."""

    @classmethod
    def setUpClass(cls):
        """Setup test data and directories once for all tests."""
        cls.test_output_dir = Path("test_outputs")
        cls.test_output_dir.mkdir(exist_ok=True)

        # Load all test datasets
        cls.datasets = []
        cls.targets = []
        for i in range(1, 4):
            dataset = pd.read_csv(f"test_data/test_data_classification_location{i}.csv")
            cls.targets.append(dataset["target"])
            cls.datasets.append(dataset.drop(columns=["target"]))

    def setUp(self):
        """Initialize fresh models for each test."""
        self.fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add"
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        pass

    def get_model_path(self, model_name):
        """Generate consistent path for model files."""
        return str(self.test_output_dir / f"{model_name}.pkl")

    def train_and_save_local_models(self):
        """Helper method to train and save local models."""
        local_models = []
        for site_idx in range(3):
            site_id = str(site_idx + 1)

            sk_learn_params = {
                "n_estimators": 105,
                "max_depth": 6,
                "random_state": 43
            }

            local_rf = LocalRandomForestClassifier(
                self.fed_rf,
                site_id=site_id,
                **sk_learn_params
            )

            X_train, X_test, y_train, y_test = train_test_split(
                self.datasets[site_idx],
                self.targets[site_idx],
                test_size=0.2,
                random_state=42
            )

            local_rf.fit(X_train, y_train)
            save_path = self.get_model_path(f"local_rf{site_id}")
            local_rf.save_model(save_location_path=save_path)
            local_models.append(local_rf)
        return local_models

    def create_federated_model(self):
        """Helper method to create and save federated model."""
        local_models = []
        for site_id in range(1, 4):
            local_rf = LocalRandomForestClassifier(self.fed_rf, site_id=str(site_id))
            loaded_model = local_rf.load_model(self.get_model_path(f"local_rf{site_id}"))
            local_models.append(loaded_model)

        fed_model = self.fed_rf.aggregate_local_models(local_models)
        save_path = self.get_model_path("fed_rf_add")
        fed_model.save_model(save_location_path=save_path)
        return fed_model


class TestPipeline(FedRFTestBase):
    """Test full pipeline in correct order."""

    def test_1_local_model_training(self):
        """Test training and saving of local models."""
        local_models = self.train_and_save_local_models()
        self.assertEqual(len(local_models), 3)

        for site_idx, model in enumerate(local_models):
            save_path = self.get_model_path(f"local_rf{site_idx + 1}")
            self.assertTrue(os.path.exists(save_path))

    def test_2_model_loading(self):
        """Test loading of local models."""
        for site_idx in range(3):
            site_id = str(site_idx + 1)
            local_rf = LocalRandomForestClassifier(self.fed_rf, site_id=site_id)
            model_path = self.get_model_path(f"local_rf{site_id}")

            self.assertTrue(os.path.exists(model_path))
            loaded_rf = local_rf.load_model(model_path)
            self.assertIsInstance(loaded_rf, LocalRandomForestClassifier)
            self.assertEqual(loaded_rf.site_id, site_id)

    def test_3_model_aggregation(self):
        """Test aggregation of local models into federated model."""
        fed_model = self.create_federated_model()
        save_path = self.get_model_path("fed_rf_add")
        self.assertTrue(os.path.exists(save_path))

    def test_4_federated_predictions(self):
        """Test predictions using federated model."""
        fed_model_path = self.get_model_path("fed_rf_add")
        self.assertTrue(os.path.exists(fed_model_path),
                        "Federated model file not found. Run aggregation test first.")

        for site_idx in range(3):
            site_id = str(site_idx + 1)

            X_train, X_test, y_train, y_test = train_test_split(
                self.datasets[site_idx],
                self.targets[site_idx],
                test_size=0.2,
                random_state=42
            )

            fed_rf = FederatedRandomForestClassifier(tree_aggregation_method="add")
            fed_rf = fed_rf.load_model(fed_model_path)

            sklearn_params = {
                "n_estimators": 105,
                "max_depth": 6,
                "random_state": 43
            }

            local_rf = LocalRandomForestClassifier(fed_rf, site_id=site_id, **sklearn_params)
            local_rf = local_rf.load_model(self.get_model_path(f"local_rf{site_id}"))

            # check if the sklearn_params are in the local_rf.params
            for k,v in sklearn_params.items():
                self.assertEqual(local_rf.params[k], v)

            local_preds = local_rf.predict(X_test, use_updated_federated_model=False)

            local_rf.commit_local_random_forest()
            local_rf.get_updated_trees_from_federated_model()

            fed_preds = local_rf.predict(X_test, use_updated_federated_model=True)

            self.assertEqual(len(local_preds), len(fed_preds))
            self.assertEqual(len(local_preds), len(y_test))

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

if __name__ == '__main__':
    unittest.main()