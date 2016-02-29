
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class DB_UserLocationHistoryHub(RelationalDBHub):
    def __init__(self):
        super(DB_UserLocationHistoryHub, self).__init__("UserLocationHistory")

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
