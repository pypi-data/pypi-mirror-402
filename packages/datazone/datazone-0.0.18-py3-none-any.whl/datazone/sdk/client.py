from deltalake import DeltaTable

from datazone.core.common.settings import SettingsManager
from datazone.core.connections.auth import AuthService
from datazone.models.sdk.access_key import AccessKey
from datazone.models.sdk.dataset import Dataset
from datazone.models.sdk.project import Project
from datazone.utils.helpers import ensure_http


class DatazoneClient:

    def __init__(self, profile_name: str | None = None):
        """
        Initializes the DatazoneClient with the given profile name.
        Args:
            profile_name: The name of the profile to use for authentication.
            If not provided, the default profile will be used.
        """
        self.profile_name = profile_name
        self.session = AuthService.get_session(profile_name)
        self.profile = SettingsManager.get_profile(profile_name)

    def __create_access_key(self, project_id: str) -> AccessKey:
        """
        Creates an access key for the Datazone API.
        """
        response = self.session.post(
            f"{self.profile.get_service_url()}/access-key/create",
            json={"project": project_id},
        )
        if not response.ok:
            raise Exception(f"Failed to create access key: {response.text}")

        payload = response.json()
        return AccessKey(**payload)

    def get_dataset(self, entity_id: str) -> Dataset:
        """
        Fetches datasets from the Datazone API.
        """
        response = self.session.get(
            f"{self.profile.get_service_url()}/dataset/get-by-id/{entity_id}",
        )
        if not response.ok:
            raise Exception(f"Failed to fetch dataset: {response.text}")

        payload = response.json()
        return Dataset(**payload)

    def get_project(self, entity_id: str):
        """
        Fetches projects from the Datazone API.
        """
        response = self.session.get(
            f"{self.profile.get_service_url()}/project/get-by-id/{entity_id}",
        )
        if not response.ok:
            raise Exception(f"Failed to fetch project: {response.text}")
        payload = response.json()
        return Project(**payload)

    def get_dataset_delta_table(self, entity_id: str):
        """
        Fetches datasets from the Datazone API and returns them as a DeltaTable.
        """
        dataset = self.get_dataset(entity_id)
        project = self.get_project(dataset.project.id)
        access_key = self.__create_access_key(project.id)
        path = f"s3a://{project.repository_name}/main/datasets/{entity_id}"
        storage_options = {
            "AWS_ACCESS_KEY_ID": access_key.access_key_id,
            "AWS_SECRET_ACCESS_KEY": access_key.secret_access_key,
            "AWS_REGION": "us-east-1",
            "AWS_S3_ALLOW_UNSAFE_RENAME": "true",
            "AWS_ALLOW_HTTP": "true",
            "AWS_ENDPOINT": f"{ensure_http(self.profile.server_endpoint)}:3333",
            "timeout": "120s",
        }
        return DeltaTable(path, storage_options=storage_options)

    def get_dataset_as_pandas(self, id: str):
        """
        Fetches datasets from the Datazone API and returns them as a pandas DataFrame.
        """
        try:
            import pandas as pd  # noqa: F401
        except ImportError:
            raise ImportError("pandas is not installed. Please install it to use this function.")

        delta_table = self.get_dataset_delta_table(id)
        return delta_table.to_pandas()
