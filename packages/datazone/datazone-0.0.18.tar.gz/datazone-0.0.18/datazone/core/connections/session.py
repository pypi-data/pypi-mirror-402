from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException


from datazone.errors.common import DatazoneServiceError, DatazoneServiceNotAccessibleError, DatazoneAuthError


UNKNOWN_ERROR_MESSAGE = "Unknown Service Error"


class CustomHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        try:
            response = super().send(request, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            if e.response is not None:
                error = e.response.json()
                if error is not None:
                    # Auth exception control
                    if "error" in error and error["error"] == "invalid_grant":
                        raise DatazoneAuthError(detail=error)
                    else:
                        _kwargs = {"message": error["message"] if "message" in error else UNKNOWN_ERROR_MESSAGE}
                        if "detail" in error:
                            _kwargs["detail"] = error["detail"]
                        raise DatazoneServiceError(**_kwargs)
            raise DatazoneServiceNotAccessibleError


adapter = CustomHTTPAdapter()
