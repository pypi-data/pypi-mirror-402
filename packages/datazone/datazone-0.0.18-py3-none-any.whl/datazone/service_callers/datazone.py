from typing import Dict, Optional

from datazone.service_callers.base import BaseServiceCaller


class DatazoneServiceCaller(BaseServiceCaller):
    service_name = "datazone"

    @classmethod
    def get_project_with_id(cls, id: str) -> Dict:
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/project/get-by-id/{id}",
        )
        return response.json()

    @classmethod
    def create_project(cls, name: str, description: Optional[str] = None) -> Dict:
        session = cls.get_session()
        response = session.post(
            f"{cls.get_service_url()}/project/create",
            json={"name": name, "description": description},
        )
        return response.json()

    @classmethod
    def create_session(cls, project_id: str) -> Dict:
        session = cls.get_session()
        response = session.post(
            f"{cls.get_service_url()}/session/create",
            json={"project": project_id},
        )
        return response.json()

    @classmethod
    def get_transaction_list_by_dataset(cls, dataset_id):
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/transaction/list",
            params={"dataset_id": dataset_id},
        )
        return response.json()

    @classmethod
    def get_view_list_by_dataset(cls, dataset_id):
        session = cls.get_session()
        response = session.get(f"{cls.get_service_url()}/view/list-by-dataset-id/{dataset_id}")
        return response.json()

    @classmethod
    def get_sample_data(cls, dataset_id: str, transaction_id: Optional[str] = None) -> Dict:
        params = {}
        if transaction_id:
            params.update({"transaction_id": transaction_id})
        session = cls.get_session()
        response = session.get(f"{cls.get_service_url()}/dataset/get-sample-data/{dataset_id}", params=params)
        return response.json()

    @classmethod
    def execute_sql(cls, query: str, project_id: str):
        session = cls.get_session()
        response = session.post(
            f"{cls.get_service_url()}/dataset/query",
            json={"query": query, "project_id": project_id},
        )
        return response.json()

    @classmethod
    def get_execution_logs(cls, execution_id: str, cursor: Optional[str] = None):
        params: Dict = {"cursor": cursor} if cursor else {}

        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/execution/logs/{execution_id}",
            params=params,
        )
        return response.json()

    @classmethod
    def get_execution_status(cls, execution_id: str):
        session = cls.get_session()
        response = session.get(f"{cls.get_service_url()}/execution/status/{execution_id}")
        return response.json()

    @classmethod
    def run_execution_pipeline(
        cls,
        pipeline_id: str,
        transform_selection: Optional[str],
    ):
        body = {}
        if transform_selection is not None:
            body.update({"transform_selection": transform_selection})

        session = cls.get_session()
        response = session.post(
            f"{cls.get_service_url()}/execution/pipeline/{pipeline_id}",
            json=body,
        )
        return response.json()

    @classmethod
    def inspect_project(cls, project_id: str):
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/project/inspect/{project_id}",
        )
        return response.json()

    @classmethod
    def get_project_summary(cls, project_id: str):
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/project/summary/{project_id}",
        )
        return response.json()

    @classmethod
    def get_project_activities(cls, project_id: str, params: Optional[Dict] = None) -> Dict:
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/project/activities/{project_id}",
            params=params or {},
        )
        return response.json()

    @classmethod
    def run_execution_extract(cls, extract_id: str):
        session = cls.get_session()
        response = session.post(f"{cls.get_service_url()}/execution/extract/{extract_id}")
        return response.json()

    @classmethod
    def project_check(cls, project_changes: Dict):
        session = cls.get_session()
        response = session.post(f"{cls.get_service_url()}/inspect/project-check", json=project_changes)
        return response.json()

    @classmethod
    def get_repository_with_id(cls, id: str) -> Dict:
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/repository/get-by-id/{id}",
        )
        return response.json()

    @classmethod
    def create_repository(cls, name: str, description: Optional[str] = None) -> Dict:
        session = cls.get_session()
        response = session.post(
            f"{cls.get_service_url()}/repository/create",
            json={"name": name, "description": description},
        )
        return response.json()

    @classmethod
    def get_current_organisation(cls) -> Dict:
        session = cls.get_session()
        response = session.get(
            f"{cls.get_service_url()}/organisation/get-current-organisation",
        )
        response.raise_for_status()
        return response.json()
