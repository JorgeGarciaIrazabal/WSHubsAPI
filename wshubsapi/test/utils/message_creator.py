

class MessageCreator:
    @classmethod
    def create_replay_message(cls, **kwargs):
        message = cls.__get_default_replay_message()
        message.update(kwargs)
        return message

    @classmethod
    def __get_default_replay_message(cls):
        return {
            "success": True,
            "reply": "successfully completed",
            "hub": "TestHub",
            "function": "testFunction",
            "ID": 0
        }

    @classmethod
    def create_on_message_message(cls, **kwargs):
        message = cls.__get_default_on_message_message()
        message.update(kwargs)
        return message

    @classmethod
    def __get_default_on_message_message(cls):
        return {
            "hub": "TestHub",
            "function": "testFunction",
            "args": [1, "2"],
            "ID": 0
        }
