from typing import Dict, Any

from datazone.type_definitions.state import State


class ContextType:
    state: State
    resources: Dict[str, Any]
