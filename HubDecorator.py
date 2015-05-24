from inspect import getargspec
import inspect
import string
import sys
import logging
import logging.config
import os
import logging.config
from HubDecoratorConfig import HubDecoratorConfig as config

log = logging.getLogger(__name__)


# todo: make a class to story global functions and variables
class HubDecorator:
    ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase
    HUBs_DICT = {}
    HUBsJS_Strings = []
    HUBsJAVA_Strings = []

    IS_HUB_PROPERTY_STR = "is_a_hub_class"

    JS_FILE_NAME = "tornadoProtocol.js"
    JAVA_FILE_NAME = "TornadoServer.java"

    @classmethod
    def isHub(cls, obj):
        try:
            return obj.__dict__.get(cls.IS_HUB_PROPERTY_STR,False)
        except:
            return False

    @staticmethod
    def getPublicFunctions(m):
        isFunction = inspect.ismethod if sys.version_info[0] == 2 else inspect.isfunction
        return isFunction(m) and not m.__name__.startswith("_")

    @classmethod
    def constructJSFile(cls, path=""):
        with open(path + cls.JS_FILE_NAME, "w") as f:
            f.write(config.JS_WRAPPER.format(main="".join(cls.HUBsJS_Strings)))

    @classmethod
    def constructJAVAFile(cls, path, package):
        with open(path + os.sep + cls.JAVA_FILE_NAME, "w") as f:
            wrapper = config.JAVA_WRAPPER % package
            f.write(wrapper.format(main="".join(cls.HUBsJAVA_Strings)))

    @staticmethod
    def hub(cls):  # todo: check if __init__ has no parameters
        hd = HubDecorator
        JS, JAVA = range(2)

        def getArgs(m):
            args = getargspec(m).args
            for arg in ("self", "_client"):
                try:
                    args.remove(arg)
                except:
                    pass

            return args

        def getDefaultsTemplates(m, template):
            if template is None: return []
            n = getArgs(m)
            d = getargspec(m).defaults
            if d is None: return []
            return [template.format(iter=i, name=n[len(n) - len(d) + i], default=d[i]) for i in range(len(d))]

        def getJSFunctionsStr(cls, templates):
            funcStrings = []
            functions = inspect.getmembers(cls, predicate=hd.getPublicFunctions)
            for name, m in functions:
                defaults = "\n\t\t\t".join(getDefaultsTemplates(m, templates.argsCook))
                funcStrings.append(templates.function.format(name=name, args=", ".join(getArgs(m)), cook=defaults))
            return funcStrings

        def getToJsonTemplates(m, template):
            if template is None: return []
            args = getArgs(m)
            return [template.format(arg=a) for a in args]

        def getJAVAFunctionsStr(cls, templates):
            funcStrings = []
            functions = inspect.getmembers(cls, predicate=hd.getPublicFunctions)
            for name, m in functions:
                args = getArgs(m)
                types = ["TYPE_" + l for l in hd.ASCII_UpperCase[:len(args)]]
                args = [types[i] + " " + arg for i, arg in enumerate(args)]
                types = "<" + ", ".join(types) + ">" if len(types) > 0 else ""
                toJson = "\n\t\t\t".join(getToJsonTemplates(m, templates.argsCook))
                funcStrings.append(templates.function.format(name=name, args=", ".join(args), types=types, cook=toJson))
            return funcStrings

        def getHubClass(templates, mode=JS):
            if mode == JS:
                funcStrings = ",\n".join(getJSFunctionsStr(cls, templates))
            elif mode == JAVA:
                funcStrings = "\n".join(getJAVAFunctionsStr(cls, templates))

            return templates.class_.format(name=cls.__name__, functions=funcStrings)
        setattr(cls,HubDecorator.IS_HUB_PROPERTY_STR,True)
        hd.HUBsJS_Strings.append(getHubClass(config.getJSTemplates(), JS))
        hd.HUBsJAVA_Strings.append(getHubClass(config.getJAVATemplates(), JAVA))

        hd.HUBs_DICT[cls.__name__] = cls()
        return cls


if __name__ == '__main__':
    @HubDecorator
    class TestClass:
        def test(self, a=1, b=2):
            print(a, b)

        def tast(self, a=5, b=1, c=3):
            print(a, b)

    @HubDecorator
    class TestClass2:
        def test(self, a=1, b=2):
            print(a, b)

        def tast(self, a=5, b=1, c=3):
            print(a, b)

    HubDecorator.constructJAVAFile(
        "C:/Users/Jorge/SoftwareProjects/WhereAppU/app/src/main/java/com/application/jorge/whereappu/ClientHandlers",
        "com.application.jorge.whereappu.ClientHandlers")
    HubDecorator.constructJSFile()
