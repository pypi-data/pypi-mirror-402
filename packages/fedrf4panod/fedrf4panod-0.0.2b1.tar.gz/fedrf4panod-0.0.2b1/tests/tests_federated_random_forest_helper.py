import unittest

import helper as test_helper
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from fedrf4panod.federated_random_forest_classifier.federated_random_forest_cls import (
    FederatedRandomForestClassifier,
)
from fedrf4panod.federated_random_forest_classifier.local_random_forest_cls import (
    LocalRandomForestClassifier,
)
from fedrf4panod.federated_random_forest_helper import (
    calculate_sampling_probability_for_each_tree,
    check_aggregation_method_for_weighted_sampling,
    check_if_element_is_valid,
    check_if_mapping_is_possible_for_tree,
    delete_site_info_from_trees,
    determine_random_state,
    determine_total_sample_size,
    get_column_id_transformation_mapping,
    group_list_by_attribute_values_of_objects,
    replace_ids_in_tree_with_new_ids,
    replace_trees_with_same_id,
    sample_trees,
    sample_trees_based_on_prob,
    set_trees_per_sample_size_rate_if_needed,
    transform_trees_to_different_feature_mapping,
)
from fedrf4panod.local_random_forest_helper import generate_feature_mapping


class TestCheckIfElementIsValid(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.valid_elements = [0.5, "valid", 1]

    def test_true_int(self):
        test_element = 1
        self.assertEqual(
            1, check_if_element_is_valid(test_element, self.valid_elements)
        )

    def test_true_float(self):
        test_element = 0.5
        self.assertEqual(
            0.5, check_if_element_is_valid(test_element, self.valid_elements)
        )

    def test_true_string(self):
        test_element = "valid"
        self.assertEqual(
            "valid", check_if_element_is_valid(test_element, self.valid_elements)
        )

    def test_false_int(self):
        with self.assertRaises(TypeError):
            test_element = 2
            check_if_element_is_valid(test_element, self.valid_elements)

    def test_false_float(self):
        with self.assertRaises(TypeError):
            test_element = 0.6
            check_if_element_is_valid(test_element, self.valid_elements)

    def test_false_string(self):
        with self.assertRaises(TypeError):
            test_element = "invalid"
            check_if_element_is_valid(test_element, self.valid_elements)


class TestDetermineRandomState(unittest.TestCase):

    def test_random_state_in_param_dict(self):
        param_dict = {"test-1": 0.5, "test-2": 2, "random_state": 42}
        self.assertEqual(42, determine_random_state(param_dict))

    def test_random_state_not_in_param_dict(self):
        param_dict = {"test-1": 0.5, "test-2": 2}
        self.assertEqual(None, determine_random_state(param_dict))


class TestSetTreesPerSampleSizeRateIfNeeded(unittest.TestCase):

    def test_sample_size_rate_is_method_and_rate_is_set(self):
        method = "trees-per-sample-size-rate"
        rate = 0.5
        self.assertEqual(0.5, set_trees_per_sample_size_rate_if_needed(method, rate))

    def test_sample_size_rate_is_method_and_rate_is_not_set(self):
        method = "trees-per-sample-size-rate"
        rate = None
        with self.assertRaises(ValueError):
            set_trees_per_sample_size_rate_if_needed(method, rate)

    def test_sample_size_rate_is_not_method_and_rate_is_set(self):
        method = "other-method"
        rate = 0.5
        with self.assertRaises(ValueError):
            set_trees_per_sample_size_rate_if_needed(method, rate)

    def test_sample_size_rate_is_not_method_and_rate_is_none(self):
        method = "other-method"
        rate = None
        self.assertEqual(None, set_trees_per_sample_size_rate_if_needed(method, rate))


class TestCheckAggregationMethodForWeightedSampling(unittest.TestCase):

    def test_weighted_sampling_and_constant_aggregation(self):
        weighting_method = "weighted-sampling"
        aggregation_method = "constant"
        # Expect no error
        check_aggregation_method_for_weighted_sampling(
            weighting_method=weighting_method, aggregation_method=aggregation_method
        )

    def test_weighted_sampling_and_add_aggregation(self):
        weighting_method = "weighted-sampling"
        aggregation_method = "add"
        # Expect value error
        with self.assertRaises(ValueError):
            check_aggregation_method_for_weighted_sampling(
                weighting_method=weighting_method, aggregation_method=aggregation_method
            )

    def test_non_weighted_sampling_and_constant_aggregation(self):
        weighting_method = "trees-per-sample-size-rate"
        aggregation_method = "constant"
        # Expect no error
        check_aggregation_method_for_weighted_sampling(
            weighting_method=weighting_method, aggregation_method=aggregation_method
        )

    def test_non_weighted_sampling_and_add_aggregation(self):
        weighting_method = "trees-per-sample-size-rate"
        aggregation_method = "add"
        # Expect no error
        check_aggregation_method_for_weighted_sampling(
            weighting_method=weighting_method, aggregation_method=aggregation_method
        )


class TestDetermineTotalSampleSize(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            weighting="weighted-sampling",
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        # Train model 1 on first 10 samples
        local_rf_1.fit(X.iloc[:10], y.iloc[:10])
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        # Train model 2 on first 20 samples
        local_rf_2.fit(X.iloc[:20], y.iloc[:20])
        # Trees should be annotated due to weighting="weighted-sampling"
        annotated_trees_site_1 = local_rf_1.estimators_
        annotated_trees_site_2 = local_rf_2.estimators_
        annotated_trees_all_sites = annotated_trees_site_1 + annotated_trees_site_2
        # Prepare dictionaries for method testing
        self.dict_site_1 = group_list_by_attribute_values_of_objects(
            list_of_objects=annotated_trees_site_1, attribute="site_id"
        )
        self.dict_all_sites = group_list_by_attribute_values_of_objects(
            list_of_objects=annotated_trees_all_sites, attribute="site_id"
        )

    def test_total_sample_size_for_one_site(self):
        total_sample_size = determine_total_sample_size(self.dict_site_1)
        self.assertEqual(total_sample_size, 10)

    def test_total_sample_size_for_multiple_sites(self):
        total_sample_size = determine_total_sample_size(self.dict_all_sites)
        self.assertEqual(total_sample_size, 30)


class TestGroupListByAttributeValuesOfElements(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            weighting="weighted-sampling",
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        # Train model 1 on first 10 samples
        local_rf_1.fit(X.iloc[:10], y.iloc[:10])
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        # Train model 2 on first 20 samples
        local_rf_2.fit(X.iloc[:20], y.iloc[:20])
        # Trees should be annotated due to weighting="weighted-sampling"
        annotated_trees_site_1 = local_rf_1.estimators_
        annotated_trees_site_2 = local_rf_2.estimators_
        self.list_of_annotated_trees = annotated_trees_site_1 + annotated_trees_site_2
        # Train a plain random forest model on the data
        rf = RandomForestClassifier(n_estimators=10)
        rf.fit(X, y)
        self.trees_from_plain_rf = rf.estimators_

    def test_error_when_attribute_is_not_available(self):
        with self.assertRaises(AttributeError):
            group_list_by_attribute_values_of_objects(
                list_of_objects=self.trees_from_plain_rf, attribute="site_size"
            )

    def test_successful_grouping(self):
        grouped_dict = group_list_by_attribute_values_of_objects(
            list_of_objects=self.list_of_annotated_trees, attribute="site_size"
        )
        keys = list(grouped_dict.keys())
        self.assertEqual(keys, [10, 20])


class TestCalculateSamplingProbabilityForEachTree(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            weighting="weighted-sampling",
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        local_rf_1 = LocalRandomForestClassifier(fed_rf)
        # Train model 1 on first 10 samples
        local_rf_1.fit(X.iloc[:10], y.iloc[:10])
        local_rf_2 = LocalRandomForestClassifier(fed_rf)
        # Train model 2 on first 20 samples
        local_rf_2.fit(X.iloc[:20], y.iloc[:20])
        local_rf_3 = LocalRandomForestClassifier(fed_rf)
        # Train model 2 on first 20 samples
        local_rf_3.fit(X.iloc[:20], y.iloc[:20])
        # Trees should be annotated due to weighting="weighted-sampling"
        self.annotated_trees_site_1 = local_rf_1.estimators_[:10]
        self.annotated_trees_site_2 = local_rf_2.estimators_[:10]
        self.annotated_trees_site_3 = local_rf_3.estimators_
        self.list_of_annotated_trees = (
            self.annotated_trees_site_1
            + self.annotated_trees_site_2
            + self.annotated_trees_site_3
        )

    def test_correct_calculation_of_sampling_probabilities_for_one_site(self):
        grouped_trees = group_list_by_attribute_values_of_objects(
            list_of_objects=self.annotated_trees_site_1, attribute="site_id"
        )
        trees, sampling_probabilities = calculate_sampling_probability_for_each_tree(
            grouped_trees_dict=grouped_trees, total_sample_size=10
        )
        # Compare the number of trees
        no_trees = len(trees)
        no_sampling_probs = len(sampling_probabilities)
        self.assertEqual(no_trees, 10)
        self.assertEqual(no_sampling_probs, 10)
        # Compare every sampling probability
        for prob in sampling_probabilities:
            self.assertEqual(prob, 0.1)
        # Check that each tree is the same as before
        test_helper.compare_trees(self, trees, self.annotated_trees_site_1)

    def test_correct_calculation_of_sampling_probabilities(self):
        grouped_trees = group_list_by_attribute_values_of_objects(
            list_of_objects=self.list_of_annotated_trees, attribute="site_id"
        )
        trees, sampling_probabilities = calculate_sampling_probability_for_each_tree(
            grouped_trees_dict=grouped_trees, total_sample_size=50
        )
        trees_1_after_slicing = trees[:10]  # 0.2 / 10
        trees_2_after_slicing = trees[10:20]  # 0.4 / 10
        trees_3_after_slicing = trees[20:120]  # 0.4 / 100
        prob_1_after_slicing = sampling_probabilities[:10]
        prob_2_after_slicing = sampling_probabilities[10:20]
        prob_3_after_slicing = sampling_probabilities[20:120]
        # Check probabilities
        sum_of_probs = 0.0
        for prob in prob_1_after_slicing:
            sum_of_probs += prob
            self.assertEqual(prob, 0.02)
        for prob in prob_2_after_slicing:
            sum_of_probs += prob
            self.assertEqual(prob, 0.04)
        for prob in prob_3_after_slicing:
            sum_of_probs += prob
            self.assertEqual(prob, 0.004)
        self.assertAlmostEqual(sum_of_probs, 1.0)
        # Check trees
        test_helper.compare_trees(
            self, trees_1_after_slicing, self.annotated_trees_site_1
        )
        test_helper.compare_trees(
            self, trees_2_after_slicing, self.annotated_trees_site_2
        )
        test_helper.compare_trees(
            self, trees_3_after_slicing, self.annotated_trees_site_3
        )


class TestSampleTreesBasedOnProb(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        rf1 = RandomForestClassifier(n_estimators=1)
        rf1.fit(X, y)
        self.tree1 = rf1.estimators_
        rf2 = RandomForestClassifier(n_estimators=1)
        rf2.fit(X, y)
        self.tree2 = rf2.estimators_
        self.trees = self.tree1 + self.tree2
        probabs_1 = [0.1]
        probabs_2 = [0.9]
        self.probabs = probabs_1 + probabs_2

    def test_compare_sample_probability_of_trees_to_actual_probability(self):
        sampled_trees = sample_trees_based_on_prob(
            trees=self.trees,
            sampling_probabilities=self.probabs,
            trees_to_sample=1000,
            random_state=42,
        )
        # Count trees for the sites
        counter_site_1 = 0
        counter_site_2 = 0
        tree1_values = self.tree1[0].tree_.value.tolist()
        tree2_values = self.tree2[0].tree_.value.tolist()
        for sampled_tree in sampled_trees:
            sampled_tree_values = sampled_tree.tree_.value.tolist()
            if sampled_tree_values == tree1_values:
                counter_site_1 += 1
            if sampled_tree_values == tree2_values:
                counter_site_2 += 1
        total = counter_site_1 + counter_site_2
        # Check that every tree has been assigned
        self.assertEqual(total, len(sampled_trees))
        self.assertGreater(counter_site_2, counter_site_1)
        # Check 800 < sampled trees from site 2 < 990
        self.assertGreater(counter_site_2, 800)
        self.assertGreater(990, counter_site_2)
        # Check 10 < sampled trees from site 1 < 200
        self.assertGreater(counter_site_1, 10)
        self.assertGreater(200, counter_site_1)
        # Check exact values (should be reproducible and always the same)
        self.assertEqual(counter_site_2, 910)
        self.assertEqual(counter_site_1, 90)


class TestDeleteSiteInfoFromTrees(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Load the data
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"]
        X = data.drop(["target"], axis=1)
        # Initialize federated model
        fed_rf = FederatedRandomForestClassifier(
            weighting="weighted-sampling",
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        local_rf_with_annotation = LocalRandomForestClassifier(fed_rf)
        # Train model
        local_rf_with_annotation.fit(X, y)
        self.trees_with_annotation = local_rf_with_annotation.estimators_
        fed_rf_2 = FederatedRandomForestClassifier(
            tree_aggregation_method="constant",
            random_state=42,
            max_depth=2,
            n_estimators=100,
        )
        local_rf_without_annotation = LocalRandomForestClassifier(fed_rf_2)
        # Train model
        local_rf_without_annotation.fit(X, y)
        self.trees_without_annotation = local_rf_without_annotation.estimators_
        example_tree_without_annotations = self.trees_without_annotation[0]
        self.expected_attributes = list(
            example_tree_without_annotations.__dict__.keys()
        )

    def test_site_id_has_been_removed(self):
        # Check that site_id is present before removal
        example_tree_with_annotations = self.trees_with_annotation[0]
        has_site_id = hasattr(example_tree_with_annotations, "site_id")
        self.assertTrue(has_site_id)
        # Check that the site_id has been removed
        trees_after_removal = delete_site_info_from_trees(self.trees_with_annotation)
        for tree in trees_after_removal:
            has_site_id = hasattr(tree, "site_id")
            self.assertFalse(has_site_id)

    def test_site_size_has_been_removed(self):
        # Check that site_size is present before removal
        example_tree_with_annotations = self.trees_with_annotation[0]
        has_site_size = hasattr(example_tree_with_annotations, "site_size")
        self.assertTrue(has_site_size)
        trees_after_removal = delete_site_info_from_trees(self.trees_with_annotation)
        for tree in trees_after_removal:
            has_site_size = hasattr(tree, "site_size")
            self.assertFalse(has_site_size)


class TestTransformTreesToDifferentFeatureMapping(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"].values
        self.X = self.data.drop("target", axis=1)
        # Create a new dataset where
        self.X_new = self.X
        # Invert the order of the columns
        self.X_new = self.X_new.rename(
            columns={
                "sepal length (cm)": "petal width (cm)",
                "sepal width (cm)": "petal length (cm)",
                "petal length (cm)": "sepal width (cm)",
                "petal width (cm)": "sepal length (cm)",
            }
        )
        self.X_one_col_missing = self.X.drop("petal width (cm)", axis=1)
        # Generate feature mappings
        self.feature_mapping = generate_feature_mapping(self.X)
        self.new_feature_mapping = generate_feature_mapping(self.X_new)
        self.feature_mapping_col_missing = generate_feature_mapping(
            self.X_one_col_missing
        )
        # Train DT's
        self.rf = RandomForestClassifier(random_state=42, max_depth=2)
        self.rf.fit(self.X, self.y)

    def test_if_every_tree_has_replaced_id(self):
        trees_with_new_ids = transform_trees_to_different_feature_mapping(
            self.rf.estimators_, self.feature_mapping, self.new_feature_mapping
        )
        # Iterate over every tree
        for i_tree, updated_tree in enumerate(trees_with_new_ids):
            old_tree = self.rf.estimators_[i_tree].tree_
            # Iterate over every feature
            for i_feature, updated_feature in enumerate(updated_tree.tree_.feature):
                # Compare new ID with old one
                if updated_feature == 0:
                    self.assertEqual(old_tree.feature[i_feature], 3)
                if updated_feature == 1:
                    self.assertEqual(old_tree.feature[i_feature], 2)
                if updated_feature == 2:
                    self.assertEqual(old_tree.feature[i_feature], 1)
                if updated_feature == 3:
                    self.assertEqual(old_tree.feature[i_feature], 0)
                if updated_feature == -2:
                    self.assertEqual(old_tree.feature[i_feature], -2)

    def test_if_number_of_trees_is_same(self):
        trees_with_new_ids = transform_trees_to_different_feature_mapping(
            self.rf.estimators_, self.feature_mapping, self.new_feature_mapping
        )
        self.assertEqual(len(trees_with_new_ids), len(self.rf.estimators_))

    def test_if_unmatched_trees_are_discarded(self):
        trees_with_new_ids = transform_trees_to_different_feature_mapping(
            self.rf.estimators_, self.feature_mapping, self.feature_mapping_col_missing
        )
        # Check if we have less trees
        self.assertNotEqual(len(trees_with_new_ids), len(self.rf.estimators_))
        # Since we use random state and fixed dataset, number of trees
        # is determined and we can test that
        self.assertEqual(len(trees_with_new_ids), 28)


class TestGetColumnIDTransformationMapping(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Base dictionary
        self.dict_1 = {"col A": 0, "col B": 1, "col C": 2, "col D": 3}
        # Different order
        self.dict_2 = {"col D": 0, "col C": 1, "col B": 2, "col A": 3}
        # Different order, non-overlapping
        self.dict_3 = {"col B": 0, "col A": 1}

    def test_equal_mapping(self):
        col_transform_dict = get_column_id_transformation_mapping(
            self.dict_1, self.dict_1
        )
        expected_mapping = {0: 0, 1: 1, 2: 2, 3: 3}
        self.assertEqual(col_transform_dict, expected_mapping)

    def test_different_order_of_columns(self):
        col_transform_dict = get_column_id_transformation_mapping(
            self.dict_1, self.dict_2
        )
        expected_mapping = {0: 3, 1: 2, 2: 1, 3: 0}
        self.assertEqual(col_transform_dict, expected_mapping)

    def test_different_order_non_overlapping(self):
        col_transform_dict = get_column_id_transformation_mapping(
            self.dict_1, self.dict_3
        )
        expected_mapping = {0: 1, 1: 0}
        self.assertEqual(col_transform_dict, expected_mapping)


class TestCheckIfMappingIsPossibleForTree(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the datasets
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"].values
        self.X = self.data.drop("target", axis=1)
        # Generate feature mappings
        dt_feature_mapping = generate_feature_mapping(self.X)
        # Create goal dictionaries
        same_columns_dict = {
            "petal length (cm)": 0,
            "sepal length (cm)": 1,
            "petal width (cm)": 2,
            "sepal width (cm)": 3,
        }
        columns_missing_dict = {"petal width (cm)": 0}
        more_columns_dict = {
            "petal length (cm)": 0,
            "sepal length (cm)": 1,
            "petal width (cm)": 2,
            "sepal width (cm)": 3,
            "new column": 4,
        }
        # Generate column ID mappings
        self.same_columns_mapping = get_column_id_transformation_mapping(
            dt_feature_mapping, same_columns_dict
        )
        self.columns_missing_mapping = get_column_id_transformation_mapping(
            dt_feature_mapping, columns_missing_dict
        )
        self.more_columns_mapping = get_column_id_transformation_mapping(
            dt_feature_mapping, more_columns_dict
        )
        # Train DT's
        self.dt = DecisionTreeClassifier(random_state=42)
        self.dt.fit(self.X, self.y)

    def test_mapping_not_possible(self):
        is_mapping_possible = check_if_mapping_is_possible_for_tree(
            self.dt, self.columns_missing_mapping
        )
        self.assertEqual(is_mapping_possible, False)

    def test_mapping_possible_every_column_matches(self):
        is_mapping_possible = check_if_mapping_is_possible_for_tree(
            self.dt, self.same_columns_mapping
        )
        self.assertEqual(is_mapping_possible, True)

    def test_mapping_possible_subset_of_columns_matches(self):
        is_mapping_possible = check_if_mapping_is_possible_for_tree(
            self.dt, self.more_columns_mapping
        )
        self.assertEqual(is_mapping_possible, True)


class TestReplaceIdsInTreeWithNewIds(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        self.data = pd.read_csv("test_data/test_data_classification.csv")
        self.y = self.data["target"].values
        self.X = self.data.drop("target", axis=1)
        # Create a new dataset where
        self.X_new = self.X
        # Invert the order of the columns
        self.X_new = self.X_new.rename(
            columns={
                "sepal length (cm)": "petal width (cm)",
                "sepal width (cm)": "petal length (cm)",
                "petal length (cm)": "sepal width (cm)",
                "petal width (cm)": "sepal length (cm)",
            }
        )
        # Generate feature mappings
        dt_feature_mapping = generate_feature_mapping(self.X)
        new_feature_mapping = generate_feature_mapping(self.X_new)
        # Generate column ID mappings
        self.column_mapping = get_column_id_transformation_mapping(
            dt_feature_mapping, new_feature_mapping
        )
        # Train DT's
        self.dt = DecisionTreeClassifier(random_state=42)
        self.dt.fit(self.X, self.y)

    def test_that_old_ids_are_correctly_replaced(self):
        updated_tree = replace_ids_in_tree_with_new_ids(self.dt, self.column_mapping)
        # Iterate over every feature
        for i, updated_feature in enumerate(updated_tree.tree_.feature):
            # Compare new ID with old one
            if updated_feature == 0:
                self.assertEqual(self.dt.tree_.feature[i], 3)
            if updated_feature == 1:
                self.assertEqual(self.dt.tree_.feature[i], 2)
            if updated_feature == 2:
                self.assertEqual(self.dt.tree_.feature[i], 1)
            if updated_feature == 3:
                self.assertEqual(self.dt.tree_.feature[i], 0)
            if updated_feature == -2:
                self.assertEqual(self.dt.tree_.feature[i], -2)


class TestSampleTrees(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"].values
        X = data.drop("target", axis=1)
        # Train Random Forest
        rf = RandomForestClassifier(random_state=42, max_depth=2, n_estimators=100)
        rf.fit(X, y)
        self.decision_tree_list = rf.estimators_

    def test_error_message(self):
        with self.assertRaises(RuntimeError):
            sample_trees(self.decision_tree_list, 101)

    def test_correct_length_of_sampling(self):
        sampled_trees = sample_trees(self.decision_tree_list, 50)
        self.assertEqual(len(sampled_trees), 50)

    def test_that_return_type_is_same_as_before(self):
        sampled_trees = sample_trees(self.decision_tree_list, 50)
        self.assertIsInstance(sampled_trees, list)
        self.assertIsInstance(sampled_trees[0], DecisionTreeClassifier)

    def test_random_state_reproducibility(self):
        # Sample two random trees
        sampled_trees = sample_trees(self.decision_tree_list, 3, random_state=42)
        # Get the tree_ objects for obtaining information
        trees = []
        for decision_tree in sampled_trees:
            trees.append(decision_tree.tree_)
        # Get the value object from the trees to make the comparison
        values = []
        for tree in trees:
            values.append(tree.value)
        sampled_trees_reproduced = sample_trees(
            self.decision_tree_list, 3, random_state=42
        )
        # Get the tree_ objects again
        trees_reproduced = []
        for decision_tree in sampled_trees_reproduced:
            trees_reproduced.append(decision_tree.tree_)
        # Get the value object from the reproduced trees to make the comparison
        values_reproduced = []
        for tree in trees_reproduced:
            values_reproduced.append(tree.value)
        # Compare the values of the trees to identify if the results were reproduced
        for i, value in enumerate(values):
            # Use np.array_equal to compare array structures
            self.assertTrue(np.array_equal(value, values_reproduced[i], equal_nan=True))


class TestReplaceTreesWithSameId(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # Load the dataset
        data = pd.read_csv("test_data/test_data_classification.csv")
        y = data["target"].values
        X = data.drop("target", axis=1)
        X_rest, X_1, y_rest, y_1 = train_test_split(
            X, y, test_size=0.5, random_state=42
        )
        X_rest, X_2, y_rest, y_2 = train_test_split(
            X_rest, y_rest, test_size=0.5, random_state=42
        )
        X_rest, self.X_3, y_rest, self.y_3 = train_test_split(
            X_rest, y_rest, test_size=0.5, random_state=42
        )
        self.fed_rf = FederatedRandomForestClassifier(
            tree_aggregation_method="add", n_estimators=2
        )
        # Train & commit local model 1
        self.lrf_1 = LocalRandomForestClassifier(self.fed_rf)
        self.lrf_1.fit(X_1, y_1)
        self.lrf_1.commit_local_random_forest()
        # Train & commit local model 2
        self.lrf_2 = LocalRandomForestClassifier(self.fed_rf)
        self.lrf_2.fit(X_2, y_2)
        self.lrf_2.commit_local_random_forest()
        # Get federated trees
        self.fed_trees = self.fed_rf.get_trees()
        # Re-train local model 2
        self.lrf_2.fit(X_rest, y_rest)
        # Combine local model 1 and re-trained local model 2 as testing reference
        self.expected_trees = self.lrf_1.get_trees() + self.lrf_2.get_trees()

    def test_error_when_site_is_not_already_in_federated_model(self):
        lrf_3 = LocalRandomForestClassifier(self.fed_rf)
        lrf_3.fit(self.X_3, self.y_3)
        trees_from_new_site = lrf_3.get_trees()
        with self.assertRaises(RuntimeError):
            replace_trees_with_same_id(
                fed_trees=self.fed_trees, local_trees=trees_from_new_site
            )

    def test_if_trees_got_replaced_correctly(self):
        # Get the trees after re-training
        new_trees_site_2 = self.lrf_2.get_trees()
        site_id_2 = self.lrf_2.site_id
        # Annotate trees with replaced attribute
        for new_tree in new_trees_site_2:
            new_tree.replaced = True
        # Replace old trees for the site with the new ones with annotation
        replaced_trees = replace_trees_with_same_id(
            fed_trees=self.fed_trees, local_trees=new_trees_site_2
        )
        # Check if every tree from this site has teh replaced attribute
        number_of_trees_after_replacement = 0
        for tree in replaced_trees:
            if tree.site_id == site_id_2:
                self.assertTrue(hasattr(tree, "replaced"))
                number_of_trees_after_replacement += 1
        # Check that all trees got replaced
        self.assertEqual(len(new_trees_site_2), number_of_trees_after_replacement)

    def test_check_same_number_of_trees_after_replacement(self):
        number_of_fed_trees_before_replacement = len(self.fed_trees)
        new_trees_site_2 = self.lrf_2.get_trees()
        replaced_trees = replace_trees_with_same_id(
            fed_trees=self.fed_trees, local_trees=new_trees_site_2
        )
        number_of_fed_trees_after_replacement = len(replaced_trees)
        self.assertEqual(
            number_of_fed_trees_before_replacement,
            number_of_fed_trees_after_replacement,
        )


if __name__ == "__main__":
    unittest.main()
