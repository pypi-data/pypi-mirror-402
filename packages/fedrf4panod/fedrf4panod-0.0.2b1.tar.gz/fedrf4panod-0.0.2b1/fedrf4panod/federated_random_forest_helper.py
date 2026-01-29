import random
from copy import deepcopy

from sklearn.tree import BaseDecisionTree, DecisionTreeClassifier, DecisionTreeRegressor


def check_if_element_is_valid(
    element_to_check,
    valid_elements: list,
    variable_name_to_check: str = "(variable name unknown)",
):
    """
    Validates whether `element_to_check` is part of the `valid_elements` list.
    If the element is valid, it returns the element. Otherwise, an error is raised.

    Parameters
    ----------
    element_to_check : any
        The element to be validated.

    valid_elements : list
        A list of valid elements against which `element_to_check` is compared.

    variable_name_to_check : str, optional
        A string representing the name of the variable being checked, used in the error message
        if validation fails.

    Returns
    -------
    any
        The valid `element_to_check` if it is found within `valid_elements`.

    """
    if element_to_check not in valid_elements:
        raise TypeError(
            f"{variable_name_to_check} is expected to be one of {valid_elements}, "
            f"got {element_to_check} instead"
        )
    else:
        return element_to_check


def determine_random_state(param_dict: dict) -> int:
    """
    Determines if the `random_state` variable is present in the given parameter dictionary.
    If found, the corresponding value is returned. Otherwise, `None` is returned.

    Parameters
    ----------
    param_dict : dict
        A dictionary containing parameter names as keys and their corresponding values.
        The method checks for the presence of the `random_state` key.

    Returns
    -------
    int or None
        The value of `random_state` if it is specified in `param_dict`.
        If not found, returns `None`.
    """
    if "random_state" in param_dict:
        return param_dict["random_state"]
    else:
        return None


def set_trees_per_sample_size_rate_if_needed(
    weighting_method: str, rate: float
) -> float:
    """
    Determines the trees-to-sample-size rate based on the selected `weighting_method`.
    If the weighting method is `trees-per-sample-size-rate`, the method checks if the
    `rate` is specified. Otherwise, it validates that `rate` is not provided for
    other weighting methods.

    Parameters
    ----------
    weighting_method : str
        The weighting method used for initialization. Must be "trees-per-sample-size-rate"
        to use the `rate` parameter.

    rate : float
        The specified trees-to-sample-size rate. This must be provided if the
        `weighting_method` is "trees-per-sample-size-rate". If `weighting_method` is
        different, `rate` should be `None`.

    Returns
    -------
    float or None
        The `rate` if the `weighting_method` is "trees-per-sample-size-rate" and the `rate` is specified.
        Returns `None` if the `weighting_method` is different and no `rate` is given.
    """
    if weighting_method == "trees-per-sample-size-rate":
        if rate is not None:
            return rate
        else:
            raise ValueError(
                f"If the parameter weighting is set to trees-per-sample-size-rate, "
                f"the parameter trees_per_sample_size_rate must be set."
            )
    else:
        if rate is None:
            return None
        else:
            raise ValueError(
                f"The parameter trees_per_sample_size_rate can only be used when the "
                f"weighting_method is set to trees-per-sample-size-rate."
            )


def group_list_by_attribute_values_of_objects(
    list_of_objects: list, attribute: str
) -> dict:
    """
    Groups a list of objects into sub-lists based on their values of the specified attribute.
    Each sub-list is stored in a dictionary where the keys are the unique attribute values,
    and the values are lists of objects sharing that attribute value.

    Parameters
    ----------
    list_of_objects : list
        A list of objects to be grouped. Each object must have the specified attribute.

    attribute : str
        The name of the attribute by which the objects will be grouped. The attribute
        must be present in all objects of `list_of_objects`.

    Returns
    -------
    dict
        A dictionary where the keys are unique values of the specified attribute, and
        the values are lists of objects from `list_of_objects` that share the same attribute value.
    """
    grouped_dict = {}
    for obj in list_of_objects:
        # Get the value of the desired attribute
        attribute_value = getattr(obj, attribute)
        # If the value occurs the first time, create the key in the dict & the list for storing the objects
        if attribute_value not in grouped_dict:
            grouped_dict[attribute_value] = []
        # Add the object to the list for the specific attribute value
        grouped_dict[attribute_value].append(obj)
    return grouped_dict


def determine_total_sample_size(
    grouped_trees_dict: dict[str, list[BaseDecisionTree]]
) -> int:
    """
    Calculates the total sample size by summing the site sizes for each site represented
    in the grouped trees. The trees must be grouped by site ID, with each site corresponding
    to a list of trees in a dictionary.

    Parameters
    ----------
    grouped_trees_dict : dict
        A dictionary where the keys are site IDs and the values are lists of trees
        associated with each site. Each tree in the list must have a `site_size` attribute,
        which represents the sample size for the respective site.

    Returns
    -------
    int
        The total sample size, calculated as the sum of the `site_size` for each site.
    """
    # Get all keys
    keys = list(grouped_trees_dict.keys())
    total_sample_size = 0
    # Go through every key
    for key in keys:
        # For each site get the site size and add this to total sum
        trees_for_site_key = grouped_trees_dict[key]
        first_tree = trees_for_site_key[
            0
        ]  # ... since site_size is the same for each site
        site_size_for_key = first_tree.site_size
        total_sample_size += site_size_for_key
    return total_sample_size


def calculate_sampling_probability_for_each_tree(
    grouped_trees_dict: dict[str, list[BaseDecisionTree]], total_sample_size: int
) -> (list[BaseDecisionTree], list[float]):
    """
    Calculates the sampling probability for each tree based on the lists grouped by the sites.
    To do this, the ratio of the number of training samples of the local sites to the total number
    of training samples across the sites is used to apply weighting according to the site size.
    The list of trees and the associated probabilities for every single tree are returned.

    Parameters
    ----------
    grouped_trees_dict : dict[str, list[BaseDecisionTree]]
        A dictionary where the keys are site IDs and the values are lists of trees
        grouped by their respective site. Each tree in the list must have a `site_size`
        attribute, representing the number of training samples for that site.

    total_sample_size : int
        The total number of training samples across all sites.

    Returns
    -------
    list[BaseDecisionTree]
        A list of trees aggregated from all sites

    list[float]
        A list of sampling probabilities corresponding to each tree
    """
    # Get all site-id's
    site_ids = list(grouped_trees_dict.keys())
    trees = []
    sampling_probabilities = []
    # Go through every site
    for site in site_ids:
        trees_for_site = grouped_trees_dict[site]
        first_tree = trees_for_site[0]
        # Determine site size
        site_size = first_tree.site_size
        # Determine number of trees for the site
        site_no_trees = len(trees_for_site)
        # Calculate sampling probability for each tree
        sampling_prob = (site_size / total_sample_size) / site_no_trees
        # Append the trees to the list of trees to return
        trees.extend(trees_for_site)
        # Append the matching sampling probability to the list of sampling probabilities
        sampling_prob_for_site = [sampling_prob] * site_no_trees
        sampling_probabilities.extend(sampling_prob_for_site)
    return trees, sampling_probabilities


def sample_trees_based_on_prob(
    trees: list[BaseDecisionTree],
    sampling_probabilities: list[float],
    trees_to_sample: int,
    random_state=None,
) -> list[BaseDecisionTree]:
    """
    Samples a specified number of trees based on the given probabilities for each tree.
    The sampling process can be made reproducible using the provided random state.

    Parameters
    ----------
    trees : list[BaseDecisionTree]
        A list of trees from which samples will be drawn. The trees can be of any type
        derived from `BaseDecisionTree`.

    sampling_probabilities : list[float]
        A list of probabilities corresponding to each tree in `trees`. These probabilities
        dictate the likelihood of each tree being selected in the sampling process.

    trees_to_sample : int
        The number of trees to sample from the list of available trees based on the given probabilities.

    random_state : int, optional
        An integer to seed the random number generator for reproducibility of the sampling process.
        If `None`, the randomness will not be seeded, leading to potentially different results
        on each run.

    Returns
    -------
    list[BaseDecisionTree]
        A list of sampled trees, where the number of trees in the list matches the specified
        `trees_to_sample`. The sampling is done according to the provided probabilities and
        the sampling may be reproducible if `random_state` is specified.
    """
    # Set a random seed to make the sampling reproducible
    if random_state is not None:
        random.seed(random_state)
    sampled_trees = random.choices(
        population=trees, weights=sampling_probabilities, k=trees_to_sample
    )
    return sampled_trees


def delete_site_info_from_trees(
    trees_to_delete_info: list[BaseDecisionTree],
) -> list[BaseDecisionTree]:
    """
    Removes site-specific information from each tree in the provided list. The method creates
    a copy of the input list and modifies it by deleting these attributes from each tree.

    Parameters
    ----------
    trees_to_delete_info : list[BaseDecisionTree]
        A list of trees, which can be instances of `DecisionTreeClassifier`, `DecisionTreeRegressor`,
        or any class derived from `BaseDecisionTree`

    Returns
    -------
    list[BaseDecisionTree]
        A list of trees with the site-specific attributes ("site_size" and "site_id") removed
    """
    # Determines which attributes should be deleted to remove all site information
    attributes_to_delete = ["site_size", "site_id"]
    # Copy the trees
    trees_without_site_info = deepcopy(trees_to_delete_info)
    # Delete attributes from every tree
    for tree in trees_without_site_info:
        # Delete all attributes
        for attribute_name in attributes_to_delete:
            if hasattr(tree, attribute_name):
                delattr(tree, attribute_name)
    return trees_without_site_info


def check_aggregation_method_for_weighted_sampling(
    weighting_method: str, aggregation_method: str
) -> None:
    """
    Validates that the aggregation method is set to "constant" if the weighting method
    is "weighted-sampling". Raises an error if this condition is not met.

    Parameters
    ----------
    weighting_method : str
        The weighting method used for initialization

    aggregation_method : str
        The aggregation method used for combining weights

    Returns
    -------
    None
    """
    if weighting_method == "weighted-sampling":
        if aggregation_method != "constant":
            raise ValueError(
                "If the weighting method is set to 'weighted-sampling', "
                "'constant' has to be set as the aggregation method"
            )
    return None


def transform_trees_to_different_feature_mapping(
    dt_classifier_list: list[BaseDecisionTree],
    current_dictionary: dict[str, int],
    new_dictionary: dict[str, int],
) -> list[BaseDecisionTree]:
    """
    Transforms the column IDs used by the decision trees to align with a new feature mapping.
    This process involves updating the column IDs in each tree according to the new dictionary
    and removing trees that cannot be mapped to the new feature schema.

    Parameters
    ----------
    dt_classifier_list : list[BaseDecisionTree]
        A list of decision trees, which can be instances of any class derived from `BaseDecisionTree`

    current_dictionary : dict[str, int]
        A dictionary mapping feature names to their current column IDs as used in the trees

    new_dictionary : dict[str, int]
        A dictionary mapping feature names to their new column IDs. The trees will be updated
        to use these new column IDs.

    Returns
    -------
    list[BaseDecisionTree]
        A list of decision trees with updated column IDs according to the new feature mapping
    """
    # Get the column id mapping
    column_id_mapping = get_column_id_transformation_mapping(
        current_dictionary, new_dictionary
    )
    trees_with_new_ids = []
    # Iterate over every tree...
    for dt_classifier in dt_classifier_list:
        # Check if all features used by the tree have a valid mapping
        if check_if_mapping_is_possible_for_tree(dt_classifier, column_id_mapping):
            # If that is the case, replace the current ID's of the tree with the new ones...
            tree_with_new_id = replace_ids_in_tree_with_new_ids(
                dt_classifier, column_id_mapping
            )
            # ... and add the tree to the trees_with_new_ids list
            trees_with_new_ids.append(tree_with_new_id)
    return trees_with_new_ids


def get_column_id_transformation_mapping(
    current_dictionary: dict[str, int], new_dictionary: dict[str, int]
) -> dict[int, int]:
    """
    Creates a mapping between current column IDs and new column IDs using two dictionaries
    that map column names to their respective IDs. The function returns a dictionary where
    the keys are the current column IDs and the values are the corresponding new column IDs.
    Column names that do not have a match in the new dictionary are excluded from the mapping.

    Parameters
    ----------
    current_dictionary : dict[str, int]
        A dictionary mapping column names to their current column IDs.

    new_dictionary : dict[str, int]
        A dictionary mapping column names to their new column IDs.

    Returns
    -------
    dict[int, int]
        A dictionary mapping current column IDs to new column IDs
    """
    # Check if we've got dictionaries to do the mapping
    if isinstance(current_dictionary, dict) & isinstance(new_dictionary, dict):
        column_id_mapping_dict = {}
        # Check every column name of the current dict
        for current_column_name in current_dictionary:
            # Get the ID of the current dict
            current_column_id = current_dictionary[current_column_name]
            # If we have the same column in new dict save the mapping
            if current_column_name in new_dictionary:
                # Map the current ID as a key and new ID as a value
                column_id_mapping_dict[current_column_id] = new_dictionary[
                    current_column_name
                ]
        return column_id_mapping_dict
    else:
        raise ValueError("Both inputs need to be dictionaries of form {str:int}")


def check_if_mapping_is_possible_for_tree(
    decision_tree: BaseDecisionTree, column_id_mapping_dict: dict[int, int]
) -> bool:
    """
    Determines if all features used in the given decision tree can be mapped
    using the provided column ID mapping dictionary. The mapping dictionary
    should contain the current column IDs and their corresponding new column IDs.

    Parameters
    ----------
    decision_tree : BaseDecisionTree
        A decision tree object for which the feature mappings need to be checked

    column_id_mapping_dict : dict[int, int]
        A dictionary mapping current column IDs to new column IDs

    Returns
    -------
    bool
        Returns `True` if every feature used in the decision tree has a corresponding
        mapping in `column_id_mapping_dict`. Returns `False` otherwise.
    """
    # Validate inputs
    if isinstance(decision_tree, DecisionTreeClassifier) or isinstance(
        decision_tree, DecisionTreeRegressor
    ):
        if isinstance(column_id_mapping_dict, dict):
            tree = decision_tree.tree_
            # Identify all splitting criteria and remove all leaves from feature list,
            # displayed as -2
            feature_list = [feature for feature in tree.feature if feature != -2]
            if all(criterion in column_id_mapping_dict for criterion in feature_list):
                return True
            else:
                return False
        else:
            raise TypeError(
                f"column_id_mapping_dict has to be a dictionary "
                f"[int, int], got {type(column_id_mapping_dict)} "
                f"instead"
            )
    else:
        raise TypeError(
            f"dt_classifier has to be "
            f"sklearn.tree.DecisionTreeClassifier, or sklearn.tree.DecisionTreeRegressor"
            f"got {type(decision_tree)} instead"
        )


def replace_ids_in_tree_with_new_ids(
    decision_tree: BaseDecisionTree, column_id_mapping_dict: dict[int, int]
) -> BaseDecisionTree:
    """
    Replaces the column IDs in the decision tree with new column IDs based on the provided mapping dictionary.
    This transformation allows the decision tree to operate with a new column schema.

    Parameters
    ----------
    decision_tree : BaseDecisionTree
        The decision tree object whose feature IDs need to be updated

    column_id_mapping_dict : dict[int, int]
        A dictionary mapping the current column IDs to new column IDs. The keys are the current
        column IDs, and the values are the corresponding new column IDs

    Returns
    -------
    BaseDecisionTree
        A decision tree object with updated column IDs, adapted to the new column schema
    """
    # Validate inputs
    if isinstance(decision_tree, DecisionTreeClassifier) or isinstance(
        decision_tree, DecisionTreeRegressor
    ):
        if isinstance(column_id_mapping_dict, dict):
            updated_features = []
            updated_tree = deepcopy(decision_tree)
            # iterate over all features of the decision tree and exchange the identifiers
            for feature_id in updated_tree.tree_.feature:
                # If the feature is a leaf (ID == -2)
                if feature_id == -2:
                    updated_features.append(-2)
                else:
                    # Replace the old feature value with the new one
                    mapped_column_id = column_id_mapping_dict[feature_id]
                    updated_features.append(mapped_column_id)
            # Not directly replaceable, therefore we have to iterate over every feature...
            for i in range(len(updated_features)):
                updated_tree.tree_.feature[i] = updated_features[i]
            # update number of features
            updated_tree.n_features = len(column_id_mapping_dict)
            updated_tree.n_features_in_ = updated_tree.n_features
        else:
            raise TypeError(
                f"column_id_mapping_dict has to be a dictionary "
                f"[int, int], got {type(column_id_mapping_dict)} "
                f"instead"
            )
    else:
        raise TypeError(
            f"dt_classifier has to be "
            f"sklearn.tree.DecisionTreeClassifier, or sklearn.tree.DecisionTreeRegressor"
            f"got {type(decision_tree)} instead"
        )

    return updated_tree


def sample_trees(
    trees: list[BaseDecisionTree], n: int, random_state=None
) -> list[BaseDecisionTree]:
    """
    Samples a subset of trees from the given list based on the specified number. The sampling
    is done randomly, and if a random state is provided, it ensures reproducibility.

    Parameters
    ----------
    trees : list[BaseDecisionTree]
        A list of decision tree objects from which the subset will be sampled

    n : int
        The number of trees to sample from the provided list

    random_state : int, optional
        An optional integer to seed the random number generator for reproducibility

    Returns
    -------
    list[BaseDecisionTree]
        A list of `BaseDecisionTree` objects representing the sampled subset
    """
    # If a random state has been specified set a seed to ensure reproducibility
    if random_state is not None:
        random.seed(random_state)
    if n > len(trees):
        raise RuntimeError(
            f"The number of the trees ({n}) that should be sampled cannot be "
            f"higher than the number of trees available ({len(trees)}) to sample from."
        )
    subset_of_trees = random.sample(trees, n)

    return subset_of_trees


def replace_trees_with_same_id(
    fed_trees: list[BaseDecisionTree], local_trees: list[BaseDecisionTree]
) -> list[BaseDecisionTree]:
    """
    Replaces trees in the federated model with new trees from the local model that share the same site ID

    Parameters
    ----------
    fed_trees : list[BaseDecisionTree]
        A list of decision tree objects representing the federated model

    local_trees : list[BaseDecisionTree]
        A list of decision tree objects representing the new local model

    Returns
    -------
    list[BaseDecisionTree]
        A list of `BaseDecisionTree` objects representing the updated federated model

    """
    # Get site ID for local trees
    local_site_id = local_trees[0].site_id
    # Remove all trees from the federated model using this ID
    trees_got_removed = False
    fed_trees_without_old_trees_from_local_site = [
        tree for tree in fed_trees if tree.site_id != local_site_id
    ]
    # Check if trees got removed
    if len(fed_trees_without_old_trees_from_local_site) < len(fed_trees):
        trees_got_removed = True
    # Extend federated model with the new trees
    if trees_got_removed:
        fed_trees_without_old_trees_from_local_site.extend(local_trees)
        fed_trees_with_replaced_local_trees = (
            fed_trees_without_old_trees_from_local_site
        )
    else:
        raise RuntimeError(
            f"replace_trees_with_same_id() got called, but the given trees cannot be replaced in "
            f"the federated model, since site {local_site_id} is not existing in the federated model trees."
        )
    return fed_trees_with_replaced_local_trees


def sample_trees_using_weighting(
    trees: list[BaseDecisionTree], number_of_local_trees: int, random_state: int
):
    """
    Samples a subset of trees based on weighted probabilities derived from their site sizes.
    The sampling process ensures that the subset reflects the differences in sample sizes across sites.

    Parameters
    ----------
    trees : list[BaseDecisionTree]
        A list of decision trees, where each tree belongs to a specific site, as indicated by its `site_id` attribute

    number_of_local_trees : int
        The number of trees to sample, which corresponds to the number of trees required at the local site

    random_state : int
        An integer seed for the random number generator to ensure reproducibility of the sampling process

    Returns
    -------
    list[BaseDecisionTree]
        A list of decision trees sampled from the original list
    """
    trees_grouped_by_site_dict = group_list_by_attribute_values_of_objects(
        list_of_objects=trees, attribute="site_id"
    )
    total_sample_size = determine_total_sample_size(
        grouped_trees_dict=trees_grouped_by_site_dict
    )
    trees, sampling_probabilities = calculate_sampling_probability_for_each_tree(
        grouped_trees_dict=trees_grouped_by_site_dict,
        total_sample_size=total_sample_size,
    )
    trees = sample_trees_based_on_prob(
        trees=trees,
        sampling_probabilities=sampling_probabilities,
        trees_to_sample=number_of_local_trees,
        random_state=random_state,
    )
    return trees
