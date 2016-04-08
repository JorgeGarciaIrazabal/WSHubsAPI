import gc
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.Hub import Hub

def removeHubsSubclasses():
    HubsInspector.HUBS_DICT.clear()
    gc.collect()
    for i in reversed(range(len(Hub.__subclasses__()))):
        del Hub.__subclasses__()[i]

    gc.collect()
