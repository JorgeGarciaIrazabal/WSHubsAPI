
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class DB_MessageHub(RelationalDBHub):
    def __init__(self):
        super(DB_MessageHub, self).__init__("Message")

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
