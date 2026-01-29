import warnings
from copy import deepcopy

import numpy as np
import pandas as pd
from sklearn.tree import BaseDecisionTree


def generate_feature_mapping(df: pd.DataFrame) -> dict[str, int]:
    """
    Creates a mapping of column names to their respective indices for the given DataFrame

    Parameters
    ----------
    df : pd.DataFrame
        A pandas DataFrame for which the feature mapping is to be generated

    Returns
    -------
    dict[str, int]
        A dictionary where each key is a column name from the DataFrame and each value is the
        corresponding column index
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"generate_feature_mapping() requires a dataset with "
            f"column names (pd.Dataframe), got "
            f"{type(df)} instead."
        )
    keys = df.columns
    values = np.arange(len(keys))
    feature_mapping = dict(zip(keys, values))
    return feature_mapping


def determine_site_size(X: pd.DataFrame) -> int:
    """
    Computes the size of the given dataset by determining the number of samples (rows) in the DataFrame

    Parameters
    ----------
    X : pd.DataFrame
        A pandas DataFrame representing the dataset for which the size is to be determined

    Returns
    -------
    int
        The number of rows in the DataFrame, representing the size of the dataset
    """
    site_size = X.shape[0]

    if site_size == 0:
        raise RuntimeError(f"The given dataset is not containing any samples!")

    return site_size


def determine_adjusted_number_of_trees_for_rate_based_weighting(
    rate: float, n: int
) -> int:
    """
    Calculates the number of trees to be used for training the model based on the given rate
    and the number of training samples

    Parameters
    ----------
    rate : float
        The rate that determines how many trees should be used per sample
    n : int
        The number of training samples

    Returns
    -------
    int
        The number of trees to use for training, adjusted based on the rate and sample size
    """
    # Calculate number of trees to be sampled
    number_of_trees_to_use = rate * n
    # Round to integer
    number_of_trees_to_use = round(number_of_trees_to_use)
    # Even though not optimal, for very low site sizes at least 1 tree
    # should be sent to the federated model
    if number_of_trees_to_use == 0:
        number_of_trees_to_use = 1
    return number_of_trees_to_use


def check_if_weighted_number_of_trees_is_not_too_small(
    weighting_method: str, site_size: int, rate: float
) -> None:
    """
    Evaluates whether the number of trees to be sent to the federated model during rate-based weighting is too small.
    If the resulting number of trees is below the threshold 5, a warning is issued to alert the user.

    Parameters
    ----------
    weighting_method : str
        The weighting method used for the model
    site_size : int
        The number of training samples at the site
    rate : float
        The rate used to determine the number of trees based on the site size

    Returns
    -------
    None
        This method does not return a value but issues a warning if the number of weighted trees is below the threshold.
    """
    if weighting_method == "trees-per-sample-size-rate":
        number_of_trees_after_weighting = site_size * rate
        if number_of_trees_after_weighting < 5:
            warnings.warn(
                f"Number of weighted trees will be very small based on the "
                f"specified rate of the federated model ({number_of_trees_after_weighting}). "
                f"Consider using a larger dataset for this site or define a different federated model."
            )


def annotate_trees_with_attribute(
    trees: list[BaseDecisionTree], attribute_value, attribute_name: str
) -> list[BaseDecisionTree]:
    """
    Adds a specified attribute with a given value to each tree in the list. The attribute is added only if
    it does not already exist in the tree. If the attribute already exists, a RuntimeError is raised.

    Parameters
    ----------
    trees: list[BaseDecisionTree]
        A list of decision trees to be annotated
    attribute_value:
        The value to assign to the new attribute in each tree
    attribute_name: str
        The name of the attribute to be added to each tree

    Returns
    -------
    list[BaseDecisionTree]
        A list of decision trees with the new attribute added
    """
    annotated_trees = []
    for tree in trees:
        # Copy the tree
        annotated_tree = deepcopy(tree)
        if not hasattr(tree, attribute_name):
            # Annotate tree with the attribute
            setattr(annotated_tree, attribute_name, attribute_value)
            # Add tree to the return list of trees
            annotated_trees.append(annotated_tree)
        else:
            raise RuntimeError(
                f"Attribute {attribute_name} already exists and cannot be set."
            )
    return annotated_trees


def select_correct_model_for_prediction(
    local_rf, use_updated_federated_model: bool
) -> [BaseDecisionTree]:
    """
    Selects the appropriate model for prediction

    Parameters
    ----------
    local_rf: LocalRandomForestClassifier or LocalRandomForestRegressor
        An instance of LocalRandomForestClassifier or LocalRandomForestRegressor from which the model
        for prediction will be selected
    use_updated_federated_model: bool
        A flag indicating whether to use the updated federated model for prediction. If True, the method
        will attempt to use the updated model. Otherwise, it will use the local model.

    Returns
    -------
    list[BaseDecisionTree]
        A list of decision trees representing the selected model for prediction. If
        `use_updated_federated_model` is True, the method returns the updated model if available;
        otherwise, it returns the local model.
    """

    # When the updated model should be used
    if use_updated_federated_model:
        # Check that updated model is available
        if hasattr(local_rf, "updated_estimators_"):
            # Return updated model to use it for prediction
            return local_rf.updated_estimators_
        else:
            raise RuntimeError(
                f"Updated model can only be for prediction, "
                f"when it has been retrieved before. \n\n "
                f"Use LocalRandomForest."
                f"get_updated_trees_from_federated_model() "
                f"to do that in advance."
            )
    else:
        # When local model should be used return local model
        if hasattr(local_rf, "local_estimators_"):
            return local_rf.local_estimators_
        else:
            try:
                local_rf.get_local_trees()
                return local_rf.local_estimators_
            except AttributeError:
                raise RuntimeError(
                    f"Local model can only be used for prediction, "
                    f"when it has been retrieved before. \n\n "
                    f"Use LocalRandomForest."
                    f"get_local_trees() to do that in advance."
                )


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


def set_trees_per_sample_size_rate_if_needed(
    weighting_method: str, rate: float
) -> float or None:
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
