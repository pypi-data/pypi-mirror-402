import json
import os
from pathlib import Path
from typing import Optional

import yaml
from bson import ObjectId
from pydantic import ValidationError

from datazone.constants import Constants
from datazone.errors.common import (
    DatazoneConfigParseError,
    DatazoneConfigFileNotExistError,
)
from datazone.models.config import Config, Pipeline


class ConfigReader:
    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path or Constants.DEFAULT_CONFIG_FILE_NAME

        if not self.is_config_file_exist():
            raise DatazoneConfigFileNotExistError

    def get_config_file_content(self) -> str:
        """Get config file content."""
        with open(self.config_file_path) as f:
            config = f.read()
        return config

    def read_config_file(self) -> Config:
        """
        Read config file and return it as a dictionary.
        Returns:
            config as a Config instance
        """
        config = self.get_config_file_content()
        data = yaml.load(config, Loader=yaml.FullLoader)
        try:
            config_instance = Config(**data)
            return config_instance
        except ValidationError as ex:
            raise DatazoneConfigParseError(detail={"errors": ex.errors()})

    def is_config_file_exist(self) -> bool:
        """Check if config file exist."""
        config_file_path = Path(self.config_file_path)
        return os.path.exists(config_file_path)

    def add_new_pipeline(self, pipeline_path: str):
        pipeline_id = ObjectId()

        file = self.read_config_file()
        file.pipelines.append(
            Pipeline(alias=str(pipeline_id), path=Path(pipeline_path)),
        )

        with open(self.config_file_path, "w") as fp:
            yaml.dump(
                json.loads(json.dumps(file.dict(exclude_none=True), default=str)),
                fp,
                Dumper=yaml.SafeDumper,
                default_flow_style=False,
                sort_keys=False,
            )
