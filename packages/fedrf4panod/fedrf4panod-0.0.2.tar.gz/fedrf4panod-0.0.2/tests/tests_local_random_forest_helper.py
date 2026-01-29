import unittest
import uuid
import warnings

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from fedrf4panod import FederatedRandomForestClassifier, LocalRandomForestClassifier
from fedrf4panod.local_random_forest_helper import (
    annotate_trees_with_attribute,
    check_if_weighted_number_of_trees_is_not_too_small,
    determine_adjusted_number_of_trees_for_rate_based_weighting,
    determine_site_size,
    generate_feature_mapping,
    select_correct_model_for_prediction,
)


class TestGenerateFeatureMapping(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.data = self.data.drop("target", axis=1)
        self.feature_mapping_dict = generate_feature_mapping(self.data)

    def test_if_all_features_included(self):
        keys = self.feature_mapping_dict.keys()
        columns = self.data.columns
        # Check number of columns
        self.assertEqual(len(keys), len(columns))
        for col in columns:
            self.assertIn(col, keys)

    def test_if_idx_are_matching(self):
        # Manual check of correct matching
        self.assertEqual(self.feature_mapping_dict["sepal length (cm)"], 0)
        self.assertEqual(self.feature_mapping_dict["sepal width (cm)"], 1)
        self.assertEqual(self.feature_mapping_dict["petal length (cm)"], 2)
        self.assertEqual(self.feature_mapping_dict["petal width (cm)"], 3)


class TestDetermineSiteSize(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = data["target"].values
        self.X = data.drop("target", axis=1)

    def test_check_if_number_determined_is_equal_to_row_size(self):
        self.assertEqual(len(self.X), determine_site_size(self.X))

    def test_error_when_dataframe_doesnt_contain_any_row(self):
        # Create an empty DataFrame
        empty_df = pd.DataFrame()
        with self.assertRaises(RuntimeError):
            determine_site_size(empty_df)


class TestDetermineAdjustedNumberOfTreesForWeighting(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"].values
        X = data.drop("target", axis=1)
        # Train Random Forest to obtain some sort of decision tree list
        rf = RandomForestClassifier(random_state=42, max_depth=2, n_estimators=100)
        rf.fit(X, y)
        self.decision_tree_list = rf.estimators_

    def test_check_if_calculated_number_is_correct(self):
        list_of_site_sizes = [1, 1, 10, 20, 20, 100]
        list_of_rates = [0.6, 10, 0.333, 0.7, 5, 1]
        expected_number_of_trees = [1, 10, 3, 14, 100, 100]
        for i, site_size in enumerate(list_of_site_sizes):
            rate = list_of_rates[i]
            expected = expected_number_of_trees[i]
            determined = determine_adjusted_number_of_trees_for_rate_based_weighting(
                rate=rate, n=site_size
            )
            self.assertEqual(determined, expected)

    def test_check_rounding_down(self):
        site_size = 10
        rate = 0.33333333
        expected = 3
        determined = determine_adjusted_number_of_trees_for_rate_based_weighting(
            rate=rate, n=site_size
        )
        self.assertEqual(determined, expected)

    def test_check_rounding_up(self):
        site_size = 10
        rate = 0.26
        expected = 3
        determined = determine_adjusted_number_of_trees_for_rate_based_weighting(
            rate=rate, n=site_size
        )
        self.assertEqual(determined, expected)

    def test_check_that_number_of_trees_wont_be_zero(self):
        site_size = 10
        rate = 0.01
        expected = 1
        determined = determine_adjusted_number_of_trees_for_rate_based_weighting(
            rate=rate, n=site_size
        )
        self.assertEqual(determined, expected)


class TestCheckIfWeightedNumberOfTreesIsNotTooSmall(unittest.TestCase):

    def test_no_warning(self):
        n = 10
        rate = 0.5
        # Catch all the warnings in w
        with warnings.catch_warnings(record=True) as w:
            check_if_weighted_number_of_trees_is_not_too_small(
                weighting_method="trees-per-sample-size-rate", site_size=n, rate=rate
            )
            # Check the warning hasn't been triggered
            self.assertEqual(len(w), 0)

    def test_throw_warning(self):
        n = 10
        rate = 0.4
        with self.assertWarns(Warning):
            check_if_weighted_number_of_trees_is_not_too_small(
                weighting_method="trees-per-sample-size-rate", site_size=n, rate=rate
            )


class TestAnnotateTreesWithAttribute(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the dataset
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"].values
        self.X = self.data.drop("target", axis=1)
        # Train DT's
        self.rf = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=2)
        self.rf.fit(self.X, self.y)
        self.trees = self.rf.estimators_

    def test_if_all_trees_are_annotated(self):
        site_id = str(uuid.uuid4())
        site_size = len(self.X)
        trees_with_site_size = annotate_trees_with_attribute(
            trees=self.trees, attribute_value=site_size, attribute_name="site_size"
        )
        annotated_trees = annotate_trees_with_attribute(
            trees=trees_with_site_size,
            attribute_value=site_id,
            attribute_name="site_id",
        )
        # Check if every tree has the same values for the desired attributes
        for tree in annotated_trees:
            self.assertEqual(tree.site_size, site_size)
            self.assertEqual(tree.site_id, site_id)


class TestSelectCorrectModelForPrediction(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        y = self.data["target"]
        X_1 = self.data.drop(["target"], axis=1)
        X_2 = self.data.drop(["target"], axis=1)
        # Do train-test split
        self.X_train_1, self.X_test_1, self.y_train_1, self.y_test_1 = train_test_split(
            X_1, y, test_size=0.2, random_state=42
        )
        # Do train-test split
        self.X_train_2, self.X_test_2, self.y_train_2, self.y_test_2 = train_test_split(
            X_2, y, test_size=0.2, random_state=42
        )
        fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", random_state=42, n_estimators=100
        )
        # Train, fit, and commit model 1
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        local_rf_1.fit(self.X_train_1, self.y_train_1)
        local_rf_1.commit_local_random_forest()
        self.local_rf_2 = LocalRandomForestClassifier(fed_rf)
        self.local_rf_2.fit(self.X_train_2, self.y_train_2)
        self.local_rf_2.commit_local_random_forest()
        self.local_rf_2.get_updated_trees_from_federated_model()

    def test_correct_selection_of_updated_model(self):
        selected_model = select_correct_model_for_prediction(
            self.local_rf_2, use_updated_federated_model=True
        )
        self.assertEqual(len(selected_model), 200)

    def test_correct_selection_of_old_model(self):
        selected_model = select_correct_model_for_prediction(
            self.local_rf_2, use_updated_federated_model=False
        )
        self.assertEqual(len(selected_model), 100)


if __name__ == "__main__":
    unittest.main()
