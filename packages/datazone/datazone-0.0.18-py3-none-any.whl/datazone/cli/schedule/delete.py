from rich import print

from datazone.service_callers.crud import CrudServiceCaller


def delete(schedule_id: str):
    CrudServiceCaller(entity_name="schedule").delete_entity(entity_id=schedule_id)
    print("Schedule has deleted successfully :fire:")
