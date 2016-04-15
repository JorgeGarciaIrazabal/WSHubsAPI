import gc
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hub import Hub

def removeHubsSubclasses():
    HubsInspector.HUBS_DICT.clear()
    gc.collect()
    for i in reversed(range(len(Hub.__subclasses__()))):
        del Hub.__subclasses__()[i]

    gc.collect()
