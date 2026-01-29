from CityOfBinds.utils.file_path_generator import FilePathGenerator


class TestPathGenerator:
    def test_default_generator_should_return_correct_files_without_folders(self):
        # arrange
        path_generator = FilePathGenerator(file_count=256)  # No folders
        # act / assert
        assert str(path_generator[0]) == "00"
        assert str(path_generator[1]) == "01"
        assert str(path_generator[10]) == "0A"
        assert str(path_generator[16]) == "10"
        assert str(path_generator[100]) == "64"
        assert str(path_generator[254]) == "FE"
        assert str(path_generator[255]) == "FF"

    def test_default_generator_should_return_correct_files_with_folders(self):
        # arrange
        path_generator = FilePathGenerator(file_count=65536)
        # act / assert
        assert str(path_generator[0]) == "00/00"
        assert str(path_generator[1]) == "00/01"
        assert str(path_generator[255]) == "00/FF"
        assert str(path_generator[256]) == "01/00"
        assert str(path_generator[257]) == "01/01"
        assert str(path_generator[65534]) == "FF/FE"
        assert str(path_generator[65535]) == "FF/FF"

    def test_default_generator_should_return_efficiently_padded_paths(self):
        # arrange
        path_generator = FilePathGenerator(file_count=4096)
        # act / assert
        assert str(path_generator[0]) == "0/00"
        assert str(path_generator[1]) == "0/01"
        assert str(path_generator[255]) == "0/FF"
        assert str(path_generator[256]) == "1/00"
        assert str(path_generator[257]) == "1/01"
        assert str(path_generator[4094]) == "F/FE"
        assert str(path_generator[4095]) == "F/FF"

    def test_default_generator_should_return_efficiently_padded_paths_edge_case(self):
        # arrange
        path_generator = FilePathGenerator(file_count=257)
        # act / assert
        assert str(path_generator[0]) == "0/00"
        assert str(path_generator[1]) == "0/01"
        assert str(path_generator[255]) == "0/FF"
        assert str(path_generator[256]) == "1/00"

    def test_default_generator_should_return_correct_root_folder_length_edge_case(self):
        # arrange
        path_generator = FilePathGenerator(file_count=4097)
        # act / assert
        assert str(path_generator[0]) == "00/00"
        assert str(path_generator[1]) == "00/01"
        assert str(path_generator[255]) == "00/FF"
        assert str(path_generator[256]) == "01/00"
        assert str(path_generator[257]) == "01/01"
        assert str(path_generator[4094]) == "0F/FE"
        assert str(path_generator[4095]) == "0F/FF"
        assert str(path_generator[4096]) == "10/00"

    def test_default_generator_should_return_correct_paths_with_small_folder_capacity(
        self,
    ):
        # arrange
        path_generator = FilePathGenerator(file_count=20, max_files_per_folder=5)
        # act / assert
        assert str(path_generator[0]) == "0/0"
        assert str(path_generator[1]) == "0/1"
        assert str(path_generator[2]) == "0/2"
        assert str(path_generator[3]) == "0/3"
        assert str(path_generator[4]) == "0/4"
        assert str(path_generator[5]) == "1/0"
        assert str(path_generator[6]) == "1/1"
        assert str(path_generator[19]) == "3/4"

    def test_default_generator_should_return_correct_paths_with_large_folder_capacity(
        self,
    ):
        # arrange
        path_generator = FilePathGenerator(file_count=256, max_files_per_folder=1000)
        # act / assert
        assert str(path_generator[0]) == "00"
        assert str(path_generator[1]) == "01"
        assert str(path_generator[10]) == "0A"
        assert str(path_generator[19]) == "13"
