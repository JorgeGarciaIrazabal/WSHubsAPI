
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class DB_User_EventHub(RelationalDBHub):
    def __init__(self):
        super(DB_User_EventHub, self).__init__("User_Event")

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
