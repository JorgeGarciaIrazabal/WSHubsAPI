# coding=utf-8
from collections import OrderedDict
import json
import logging
import sys

__author__ = 'jgarc'
from inspect import getargspec

FUNCTION_MESSAGE = """Function "%s" called.
    Parameters used: %s
    Result: %s
"""
strBasicObjects =  [str,unicode] if sys.version_info[0] == 2 else [str]
basicObjectList = [list, dict, str, strBasicObjects, int, float, bool, type(None)]
basicObjectList.extend(strBasicObjects)
MAX_STRING_LENGTH = 400

log = logging.getLogger(__name__)

class LogFunction:

    @staticmethod
    def debug(func):
        return LogFunction.__log(func, log.debug)

    @staticmethod
    def info(func):
        return LogFunction.__log(func, log.info)

    @staticmethod
    def warning(func):
        return LogFunction.__log(func, log.warning)

    @staticmethod
    def error(func):
        return LogFunction.__log(func, log.error)

    @staticmethod
    def critical(func):
        return LogFunction.__log(func, log.critical)

    @staticmethod
    def __log(func, logFunc):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            parameters = OrderedDict()
            specs = getargspec(func)
            argsName = specs[0]
            for i, arg in enumerate(args):
                if i >= len(argsName):
                    parameters["args"] = str(args[i:])
                else:
                    if isinstance(args[i], basicObjectList):
                        parameters[argsName[i]] = args[i]
                    else:
                        parameters[argsName[i]] = str(args[i])
            for key, value in kwargs.items():
                if isinstance(value, basicObjectList):
                    parameters[key] = value
                else:
                    parameters[key] = str(value)

            if not isinstance(result, basicObjectList):
                result = str(result)

            try:
                parameters.pop("self")
            except:
                pass
            parameters = json.dumps(parameters, separators=(',', ' = '))
            if len(parameters) >= MAX_STRING_LENGTH: parameters = parameters[:MAX_STRING_LENGTH - 3] + "..."
            if isinstance(result, (str, unicode)) and len(result) >= MAX_STRING_LENGTH:
                result = result[:MAX_STRING_LENGTH - 3] + "..."
            logFunc(FUNCTION_MESSAGE % (func.__name__, parameters, result))
            return result

        return wrapper
