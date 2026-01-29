from datazone.errors.base import DatazoneError


class PipelineFunctionNotDefined(DatazoneError):
    message = "Pipeline function is not defined!"


class ModuleNotFound(DatazoneError):
    message = "Module couldn't found!"


class FileNotExist(DatazoneError):
    message = "File does not exist."
