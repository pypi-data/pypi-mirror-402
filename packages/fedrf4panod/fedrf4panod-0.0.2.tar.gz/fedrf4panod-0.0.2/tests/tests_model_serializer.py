import os
import unittest

import _pickle
from sklearn.ensemble import RandomForestClassifier

from fedrf4panod import LocalRandomForestClassifier
from fedrf4panod.model_serializer import (
    check_validity_of_filename,
    create_save_directory,
    determine_default_save_location_path,
    load_object,
    raise_error_if_file_already_exists,
    save_object,
)


class TestCreateSaveDirectory(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Get the current working directory
        self.current_dir = os.getcwd()

    def test_folder_exists_already(self):
        # Absence of errors is tested here, usually os.makedirs is throwing an error when the folder already exists,
        # but we don't want that here
        number_of_folders_before_call = len(next(os.walk(self.current_dir))[1])
        create_save_directory(self.current_dir)
        number_of_folders_after_call = len(next(os.walk(self.current_dir))[1])
        # Check that no folder has been created in the current working directory
        self.assertEqual(number_of_folders_before_call, number_of_folders_after_call)

    def test_create_new_folder(self):
        path_save_location = os.path.join(self.current_dir, "new_folder")
        # Check that folder doesn't exist beforehand
        self.assertFalse(os.path.exists(path_save_location))
        number_of_folders_before_call = len(next(os.walk(self.current_dir))[1])
        create_save_directory(path_save_location)
        number_of_folders_after_call = len(next(os.walk(self.current_dir))[1])
        # Check that folder has been created
        self.assertTrue(os.path.exists(path_save_location))
        self.assertGreater(number_of_folders_after_call, number_of_folders_before_call)
        # Delete folder after test
        os.rmdir(path_save_location)


class TestDetermineDefaultSaveLocationPath(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Get the current working directory
        self.current_dir = os.getcwd()

    def test_correct_path_return(self):
        folder = "default"
        expected_path = os.path.join(self.current_dir, folder)
        save_location = determine_default_save_location_path(folder)
        self.assertEqual(expected_path, save_location)


class TestRaiseErrorIfFileAlreadyExists(unittest.TestCase):

    def test_error_if_file_already_exists(self):
        this_filename = os.path.realpath(__file__)
        with self.assertRaises(FileExistsError):
            raise_error_if_file_already_exists(this_filename)

    def test_no_error_if_file_doesnt_exist(self):
        modified_filename = os.path.realpath(__file__) + "added_extension"
        raise_error_if_file_already_exists(modified_filename)


class TestSaveObject(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.current_dir = os.getcwd()
        self.rf = RandomForestClassifier(n_estimators=50)
        self.folder_name = "test_folder"
        self.name = "rf_1"
        self.file_name_with_extension = self.name + ".pkl"

    def test_file_created_at_existing_location(self):
        # Create the location in advance
        path = os.path.join(self.current_dir, self.folder_name)
        os.makedirs(path)
        # Save object
        save_object(self.rf, file_name=self.name, save_location_path=path)
        # Check
        complete_file_path = os.path.join(path, self.file_name_with_extension)
        self.assertTrue(os.path.isfile(complete_file_path))
        # Clean
        os.remove(complete_file_path)
        os.rmdir(path)

    def test_file_created_at_new_location(self):
        # Set up path which has to be created
        path = os.path.join(self.current_dir, self.folder_name)
        # Check that path doesn't exist in advance
        self.assertFalse(os.path.exists(path))
        # Save object
        save_object(self.rf, file_name=self.name, save_location_path=path)
        # Check
        complete_file_path = os.path.join(path, self.file_name_with_extension)
        self.assertTrue(os.path.isfile(complete_file_path))
        # Clean
        os.remove(complete_file_path)
        os.rmdir(path)

    def test_saving_with_invalid_filename(self):
        invalid_file_name = self.file_name_with_extension
        with self.assertRaises(ValueError):
            save_object(
                self.rf,
                file_name=invalid_file_name,
                default_save_folder_name="test_folder",
            )

    def test_file_created_at_default_folder(self):
        # Save object
        save_object(
            self.rf, file_name=self.name, default_save_folder_name=self.folder_name
        )
        # Determine default saving location
        file_dir = os.path.join(self.current_dir, self.folder_name)
        complete_file_path = os.path.join(file_dir, self.file_name_with_extension)
        # Check if file has been created
        self.assertTrue(os.path.isfile(complete_file_path))
        # Clean
        os.remove(complete_file_path)
        os.rmdir(file_dir)

    def test_error_no_default_folder_nor_path(self):
        with self.assertRaises(ValueError):
            save_object(self.rf, file_name=self.name)

    def test_error_overriding(self):
        # Save object
        save_object(
            self.rf, file_name=self.name, default_save_folder_name=self.folder_name
        )
        with self.assertRaises(FileExistsError):
            save_object(
                self.rf, file_name=self.name, default_save_folder_name=self.folder_name
            )
        # Clean
        file_dir = os.path.join(self.current_dir, self.folder_name)
        complete_file_path = os.path.join(file_dir, self.file_name_with_extension)
        os.remove(complete_file_path)
        os.rmdir(file_dir)


class TestLoadObject(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.current_dir = os.getcwd()
        self.rf = RandomForestClassifier(n_estimators=50)
        self.folder_name = "test_folder"
        self.name = "rf_1"
        self.file_name_with_extension = self.name + ".pkl"
        self.file_dir = os.path.join(self.current_dir, self.folder_name)
        self.complete_file_path = os.path.join(
            self.file_dir, self.file_name_with_extension
        )

    def test_error_wrong_object_type(self):
        # Save object
        save_object(
            self.rf, file_name=self.name, default_save_folder_name=self.folder_name
        )
        with self.assertRaises(TypeError):
            obj = load_object(
                cls=LocalRandomForestClassifier, file_path=self.complete_file_path
            )
        # Clean
        file_dir = os.path.join(self.current_dir, self.folder_name)
        complete_file_path = os.path.join(file_dir, self.file_name_with_extension)
        os.remove(complete_file_path)
        os.rmdir(file_dir)

    def test_error_no_pickle_file(self):
        location_to_test_csv = os.path.join(
            self.current_dir, "test_data", "test_data_classification.csv"
        )
        with self.assertRaises(_pickle.UnpicklingError):
            load_object(RandomForestClassifier, location_to_test_csv)

    def test_error_invalid_file_path(self):
        modified_path = self.complete_file_path + "invalid"
        with self.assertRaises(FileNotFoundError):
            load_object(RandomForestClassifier, file_path=modified_path)

    def test_check_attributes_of_loaded_object(self):
        # Save object
        save_object(
            self.rf, file_name=self.name, default_save_folder_name=self.folder_name
        )
        obj = load_object(cls=RandomForestClassifier, file_path=self.complete_file_path)
        # Check some attributes
        self.assertEqual(obj.n_estimators, self.rf.n_estimators)
        self.assertEqual(obj.max_depth, self.rf.max_depth)
        self.assertEqual(obj.max_features, self.rf.max_features)
        self.assertEqual(obj.max_leaf_nodes, self.rf.max_leaf_nodes)
        # Clean
        file_dir = os.path.join(self.current_dir, self.folder_name)
        complete_file_path = os.path.join(file_dir, self.file_name_with_extension)
        os.remove(complete_file_path)
        os.rmdir(file_dir)


class TestCheckValidityOfFileName(unittest.TestCase):

    def test_valid_file_name(self):
        check_validity_of_filename("test_file")

    def test_seperator_in_file_name(self):
        with self.assertRaises(ValueError):
            check_validity_of_filename("test/file")

    def test_backslash_in_file_name(self):
        with self.assertRaises(ValueError):
            check_validity_of_filename("test\\file")

    def test_extension_in_file_name(self):
        with self.assertRaises(ValueError):
            check_validity_of_filename("test.file")


if __name__ == "__main__":
    unittest.main()
