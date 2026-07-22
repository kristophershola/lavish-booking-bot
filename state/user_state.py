_user_state = {}


def get_state(sender_id):
    return _user_state.get(sender_id)


def set_state(sender_id, menu, context=None):
    _user_state[sender_id] = {
        "menu": menu,
        "context": context or {}
    }


def clear_state(sender_id):
    _user_state.pop(sender_id, None)
