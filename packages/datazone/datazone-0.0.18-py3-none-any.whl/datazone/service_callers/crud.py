from typing import Dict, Optional

from datazone.errors.common import DatazoneServiceError
from datazone.service_callers.base import BaseServiceCaller


class CrudServiceCaller(BaseServiceCaller):
    def __init__(self, entity_name: str):
        self.entity_name = entity_name

    def get_entity_with_id(self, entity_id: str) -> Dict:
        response = self.get_session().get(
            f"{self.get_service_url()}/{self.entity_name}/get-by-id/{entity_id}",
        )
        if not response.ok:
            raise DatazoneServiceError(response.text)
        return response.json()

    def get_entity_list(self, params: Optional[Dict] = None):
        session = self.get_session()
        response = session.get(f"{self.get_service_url()}/{self.entity_name}/list", params=params)
        return response.json()

    def create_entity(self, payload: Dict):
        session = self.get_session()
        response = session.post(
            f"{self.get_service_url()}/{self.entity_name}/create",
            json=payload,
        )
        if not response.ok:
            raise DatazoneServiceError(response.text)

        return response.json()

    def delete_entity(self, entity_id: str):
        session = self.get_session()
        session.delete(f"{self.get_service_url()}/{self.entity_name}/delete/{entity_id}")

    def update_entity(self, entity_id: str, payload: Dict):
        session = self.get_session()
        session.put(f"{self.get_service_url()}/{self.entity_name}/update/{entity_id}", json=payload)
