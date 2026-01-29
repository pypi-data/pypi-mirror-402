import os
import pickle

import _pickle


def load_object(cls: type, file_path: str) -> object:
    """
    Loads an object of the specified class from a pickle file

    Parameters
    ----------
    cls: type
        The expected class of the object to be loaded from the pickle file
    file_path: str
        The path to the pickle file containing the serialized object

    Returns
    -------
    object
        An instance of the specified class `cls` loaded from the pickle file
    """
    try:
        with open(file_path, "rb") as pickle_file:
            # Load the serialized object from the file
            obj = pickle.load(pickle_file)
            # Ensure the loaded object is of the correct class
            if not isinstance(obj, cls):
                raise TypeError(f"Loaded object is not of type {cls.__name__}")
            return obj
    except FileNotFoundError:
        raise FileNotFoundError(f"Pickle file not found: {file_path}")
    except _pickle.UnpicklingError:
        raise _pickle.UnpicklingError(
            f"The file could not be unpickled, "
            f"please make sure that {file_path} is a pickled file."
        )


def save_object(
    object_to_save,
    file_name: str,
    default_save_folder_name: str = None,
    save_location_path: str = None,
) -> None:
    """
    Saves the specified object to a pickle file and creating the necessary directory if it does not exist.

    Parameters
    ----------
    object_to_save: object
        The object to be serialized and saved to a file
    file_name: str
        The name of the pickle file to be created, without the file extension
    default_save_folder_name: str, optional
        The default name for the save folder to use if `save_location_path` is not provided
    save_location_path: str, optional
        An optional path to the directory where the pickle file will be saved. If not provided,
        the function will use `default_save_folder_name` to determine the save location.

    Returns
    -------
    None
    """
    check_validity_of_filename(file_name)
    if default_save_folder_name is None:
        if save_location_path is None:
            raise ValueError(
                "Either 'default_save_folder_name' or 'save_location_path' have to be set in order to "
                "determine the save location."
            )
    if save_location_path is None:
        save_location_path = determine_default_save_location_path(
            default_save_folder_name
        )
    create_save_directory(save_location_path)
    file_name_with_extension = file_name + ".pkl"
    save_path = os.path.join(save_location_path, file_name_with_extension)
    raise_error_if_file_already_exists(save_path)
    with open(save_path, "wb") as file:
        pickle.dump(object_to_save, file)


def determine_default_save_location_path(default_save_folder_name: str):
    """
    Determines the absolute path for the default save location directory based on the current working directory

    Parameters
    ----------
    default_save_folder_name: str
        The name of the default folder where the object should be saved

    Returns
    -------
    str
        The absolute path to the directory where the object should be saved
    """
    # Get the current working directory
    current_dir = os.getcwd()
    path_save_location = os.path.join(current_dir, default_save_folder_name)
    return path_save_location


def create_save_directory(save_path: str) -> None:
    """
    Ensures that the directory structure for the specified path exists by creating
    the directory and any necessary parent directories.

    Parameters
    ----------
    save_path: str
        The path to the directory that should be created

    Returns
    -------
    None
    """
    # Create the directory (and subdirectories if needed)
    os.makedirs(save_path, exist_ok=True)


def raise_error_if_file_already_exists(save_path: str) -> None:
    """
    Checks if a file already exists at the specified path and raises an error
    if it does

    Parameters
    ----------
    save_path: str
        The path to the file for which existence is to be checked

    Returns
    -------
    None
    """
    if os.path.isfile(save_path):
        raise FileExistsError(f"The file {save_path} already exists.")


def check_validity_of_filename(file_name: str) -> None:
    """
    Validates the given filename to ensure it does not contain any invalid characters
    or file extensions. Raises an error if the filename is deemed invalid.

    Parameters
    ----------
    file_name: str
        The name of the file to be validated

    Returns
    -------
    None
    """
    # Check if there are any separators
    separators = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
    has_separator = any(separator in file_name for separator in separators)
    # Check if there is an extension in the filename
    has_extension = "." in file_name
    if has_extension or has_separator:
        raise ValueError(
            f"{file_name} is not a valid. The filename cannot contain an extension (.) or any of the "
            f"following separators: {separators}"
        )
