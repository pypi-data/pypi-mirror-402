import os
from pathlib import Path

import yaml
import yaml_include


class YAMLReader:
    """The YAMLReader class is responsible for reading data
    from a YAML file and returning it as a dictionary.
    """

    @classmethod
    def read_data_to_dict(cls, data_file_path: str, data_dir_path: str = "") -> dict:
        """Reads data from a YAML file and returns it as a dictionary.

        Supports both .yaml and .yml file extensions. If a file with the specified
        extension is not found, the method tries the alternative extension.

        :param data_file_path: Path to the YAML file.
        :param data_dir_path: Path to the directory containing the YAML file.

        :return: A dictionary with the data from the YAML file.
        :rtype: dict

        :raises FileNotFoundError: If the YAML file is not found.
        """
        yaml.add_constructor(
            "!include",
            yaml_include.Constructor(base_dir=data_dir_path),
            yaml.FullLoader,
        )

        # Check if the file has a yaml/yml extension
        if data_file_path.lower().endswith(".yaml"):
            # If the file ends with .yaml, try .yaml first, then .yml
            base_name = data_file_path[: -len(".yaml")]
            possible_paths = [
                str((Path(data_dir_path) / data_file_path).resolve()),  # Original .yaml
                str(
                    (Path(data_dir_path) / (base_name + ".yml")).resolve()
                ),  # Alternative .yml
            ]
        elif data_file_path.lower().endswith(".yml"):
            # If the file ends with .yml, try .yml first, then .yaml
            base_name = data_file_path[: -len(".yml")]
            possible_paths = [
                str((Path(data_dir_path) / data_file_path).resolve()),  # Original .yml
                str(
                    (Path(data_dir_path) / (base_name + ".yaml")).resolve()
                ),  # Alternative .yaml
            ]
        else:
            # If no extension is specified, try both extensions
            possible_paths = [
                str((Path(data_dir_path) / (data_file_path + ".yaml")).resolve()),
                str((Path(data_dir_path) / (data_file_path + ".yml")).resolve()),
            ]

        # Try each possible path in order
        abs_data_file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                abs_data_file_path = path
                break

        if abs_data_file_path is None:
            # If none of the paths exist, raise an error with the original path
            original_abs_path = str((Path(data_dir_path) / data_file_path).resolve())
            raise FileNotFoundError(
                f"File not found {original_abs_path!r}. Tried: {', '.join(possible_paths)}"
            )

        with open(abs_data_file_path, "r") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        return data
