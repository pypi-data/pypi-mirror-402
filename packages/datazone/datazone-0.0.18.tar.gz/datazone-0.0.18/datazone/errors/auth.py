from datazone.errors.base import DatazoneError


class DatazoneInvalidGrantError(DatazoneError):
    message = "Invalid grant"
