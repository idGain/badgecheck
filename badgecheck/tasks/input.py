import json
import re
import validators

from ..actions.input import set_input_type

from utils import task_result

"""
Helpful utils
"""
def input_is_url(user_input):
    return validators.url(input)


def input_is_json(user_input):
    try:
        value = json.loads(input)
        return True
    except ValueError:
        return False


def input_is_jws(user_input):
    jws_regex = re.compile(r'^[A-z0-9-]+.[A-z0-9-]+.[A-z0-9-_]+$')
    return bool(jws_regex.match(user_input))


"""
Input-processing tasks
"""
def detect_input_type(state):
    """
    Detects what data format user has provided and saves to the store.
    """
    input_value = state.get('input').get('value')

    if input_is_url(input_value):
        action = set_input_type('url')
    elif input_is_json(input_value):
        action = set_input_type('json')
    elif input_is_json(input_value):
        action = set_input_type('jwt')
    else:
        raise NotImplementedError("only URL or JSON input implemented so far")

    return task_result(
        message="Input of type {} detected.".format(action['input_type']),
        actions=[action]
    )