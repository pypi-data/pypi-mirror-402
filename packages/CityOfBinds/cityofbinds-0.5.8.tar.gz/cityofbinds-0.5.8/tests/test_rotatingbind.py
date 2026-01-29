import zipfile
from pathlib import Path

from CityOfBinds import BindTemplate, RotatingBind


class TestFileCreation:
    def test_simple_rotating_bind_file_creation(self, in_tmp_dir):
        # assemble
        powers = ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
        attack_bind_template = (
            BindTemplate("Q")
            .add_toggle_off_power("super speed")
            .add_toggle_off_power("sprint")
            .add_toggle_on_power("dark nova")
            .add_power_pool(powers)
            .add_toggle_off_power("dark nova")
        )
        rotating_bind = RotatingBind().add_bind_template(attack_bind_template)
        # act
        rotating_bind.publish_bind_files(parent_folder_name="my_rotate_bind")

        expected_files = [
            "my_rotate_bind/0.txt",
            "my_rotate_bind/1.txt",
            "my_rotate_bind/2.txt",
        ]

        for file_path in expected_files:
            assert Path(file_path).exists()

        with open(expected_files[0], "r") as f:
            contents = f.read()
        assert (
            contents
            == 'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/1.txt"'
        )

        with open(expected_files[1], "r") as f:
            contents = f.read()
        assert (
            contents
            == 'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/2.txt"'
        )

        with open(expected_files[2], "r") as f:
            contents = f.read()
        assert (
            contents
            == 'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/0.txt"'
        )

    def test_rotating_bind_with_multiple_binds_file_creation(self, in_tmp_dir):
        # assemble
        rotating_bind = (
            RotatingBind()
            .add_bind_template(
                BindTemplate("Q")
                .add_toggle_off_power("super speed")
                .add_toggle_off_power("sprint")
                .add_toggle_on_power("dark nova")
                .add_power_pool(
                    ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
                )
                .add_toggle_off_power("dark nova"),
            )
            .add_bind_template(
                BindTemplate("E").add_power_pool(["kick", "box", "brawl"])
            )
        )
        # act
        rotating_bind.publish_bind_files(parent_folder_name="optional_triggers")

        expected_files = [
            "optional_triggers/0.txt",
            "optional_triggers/1.txt",
            "optional_triggers/2.txt",
        ]

        for file_path in expected_files:
            assert Path(file_path).exists()

        with open(expected_files[0], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/1.txt"\n'
            'E "powexecname kick$$bindloadfilesilent optional_triggers/1.txt"'
        )

        with open(expected_files[1], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/2.txt"\n'
            'E "powexecname box$$bindloadfilesilent optional_triggers/2.txt"'
        )

        with open(expected_files[2], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/0.txt"\n'
            'E "powexecname brawl$$bindloadfilesilent optional_triggers/0.txt"'
        )

    def test_rotating_bind_with_inclusive_triggers_file_creation(self, in_tmp_dir):
        # assemble
        rotating_bind = (
            RotatingBind()
            .add_exclusive_loading_bind_template(
                BindTemplate("Q")
                .add_toggle_off_power("super speed")
                .add_toggle_off_power("sprint")
                .add_toggle_on_power("dark nova")
                .add_power_pool(
                    ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
                )
                .add_toggle_off_power("dark nova")
            )
            .add_bind_template(
                BindTemplate("E").add_power_pool(["kick", "box", "brawl"])
            )
        )
        # act
        rotating_bind.publish_bind_files(parent_folder_name="optional_triggers")

        expected_files = [
            "optional_triggers/0.txt",
            "optional_triggers/1.txt",
            "optional_triggers/2.txt",
        ]

        for file_path in expected_files:
            assert Path(file_path).exists()

        with open(expected_files[0], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/1.txt"\n'
            'E "powexecname kick"'
        )

        with open(expected_files[1], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/2.txt"\n'
            'E "powexecname box"'
        )

        with open(expected_files[2], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/0.txt"\n'
            'E "powexecname brawl"'
        )

    def test_rotating_bind_with_exclusive_triggers_file_creation(self, in_tmp_dir):
        # assemble
        rotating_bind = (
            RotatingBind()
            .add_bind_template(
                BindTemplate("Q")
                .add_toggle_off_power("super speed")
                .add_toggle_off_power("sprint")
                .add_toggle_on_power("dark nova")
                .add_power_pool(
                    ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
                )
                .add_toggle_off_power("dark nova")
            )
            .add_non_loading_bind_template(
                BindTemplate("E").add_power_pool(["kick", "box", "brawl"]),
            )
        )
        # act
        rotating_bind.publish_bind_files(parent_folder_name="optional_triggers")

        expected_files = [
            "optional_triggers/0.txt",
            "optional_triggers/1.txt",
            "optional_triggers/2.txt",
        ]

        for file_path in expected_files:
            assert Path(file_path).exists()

        with open(expected_files[0], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/1.txt"\n'
            'E "powexecname kick"'
        )

        with open(expected_files[1], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/2.txt"\n'
            'E "powexecname box"'
        )

        with open(expected_files[2], "r") as f:
            contents = f.read()
        assert contents == (
            'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova$$bindloadfilesilent optional_triggers/0.txt"\n'
            'E "powexecname brawl"'
        )


class TestArchiveCreation:
    def test_simple_rotating_bind_archive_creation(self, in_tmp_dir):
        # assemble
        powers = ["dark nova blast", "dark Nova bolt", "dark nova emmanation"]
        attack_bind_template = (
            BindTemplate("Q")
            .add_toggle_off_power("super speed")
            .add_toggle_off_power("sprint")
            .add_toggle_on_power("dark nova")
            .add_power_pool(powers)
            .add_toggle_off_power("dark nova")
        )
        rotating_bind = RotatingBind().add_bind_template(attack_bind_template)
        # act
        rotating_bind.archive_bind_files(parent_folder_name="my_rotate_bind")

        # assert - check that archive file was created
        archive_path = Path("my_rotate_bind.zip")
        assert archive_path.exists()
        assert archive_path.is_file()

        # Verify archive contains the expected files and content
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            file_list = zip_file.namelist()
            expected_files = [
                "my_rotate_bind/0.txt",
                "my_rotate_bind/1.txt",
                "my_rotate_bind/2.txt",
            ]

            # Check all expected files are in the archive
            for expected_file in expected_files:
                assert expected_file in file_list

            # Validate content of each file in the archive
            with zip_file.open("my_rotate_bind/0.txt") as f:
                contents = f.read().decode("utf-8")
                assert contents == (
                    'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova blast$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/1.txt"'
                )

            with zip_file.open("my_rotate_bind/1.txt") as f:
                contents = f.read().decode("utf-8")
                assert contents == (
                    'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova bolt$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/2.txt"'
                )

            with zip_file.open("my_rotate_bind/2.txt") as f:
                contents = f.read().decode("utf-8")
                assert contents == (
                    'Q "powexectoggleoff super speed$$powexectoggleoff sprint$$powexectoggleon dark nova$$powexecname dark nova emmanation$$powexectoggleoff dark nova$$bindloadfilesilent my_rotate_bind/0.txt"'
                )
