
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class DB_ClientLogHub(RelationalDBHub):
    def __init__(self):
        super(DB_ClientLogHub, self).__init__("ClientLog")

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
