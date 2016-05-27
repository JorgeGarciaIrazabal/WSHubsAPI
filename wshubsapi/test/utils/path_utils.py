import inspect
from os import path
import os


def get_module_path():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file_name = info.filename
    return path.dirname(path.abspath(file_name))


def get_resources_path(module=None):
    resources_path = path.dirname(get_module_path()) + os.sep + "resources"
    if module is not None:
        resources_path = path.join(resources_path, module)
    return resources_path
