
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class DB_UserHub(RelationalDBHub):
    def __init__(self):
        super(DB_UserHub, self).__init__("User")

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
