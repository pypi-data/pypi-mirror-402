from typing import Optional, Union


class DatazoneError(Exception):
    message = "Datazone Error"

    def __init__(self, message: Optional[str] = None, detail: Optional[Union[str, dict]] = None):
        super().__init__()
        if message:
            self.message = message
        self.detail = detail
