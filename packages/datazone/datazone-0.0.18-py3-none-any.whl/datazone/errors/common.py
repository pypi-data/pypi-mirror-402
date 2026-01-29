from datazone.errors.base import DatazoneError


class DatazoneAuthError(DatazoneError):
    message = "Datazone Authentication Error. You can login using `datazone auth test`."


class DatazoneServiceError(DatazoneError):
    message = "Datazone Service Error"


class DatazoneServiceNotAccessibleError(DatazoneError):
    message = "Datazone Service is not accessible."


class DatazoneProfileNotFoundError(DatazoneError):
    message = "Datazone Profile not found."


class DatazoneConfigParseError(DatazoneError):
    message = "Datazone Config Parse Error."


class DatazoneConfigFileNotExistError(DatazoneError):
    message = "Datazone Config file does not exist."


class InvalidRepositoryError(DatazoneError):
    message = "Invalid Repository. Check if the current directory is a datazone repository and it has been initialized."
