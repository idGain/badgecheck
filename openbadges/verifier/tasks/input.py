import base64
import json
from openbadges_bakery import unbake
from pyld import jsonld
import re
from tempfile import NamedTemporaryFile

from ..actions.input import set_input_type, store_input
from ..actions.tasks import add_task, report_message
from ..actions.validation_report import set_validation_subject
from ..exceptions import TaskPrerequisitesError
from ..openbadges_context import OPENBADGES_CONTEXT_V2_URI
from ..tasks.utils import is_url
from ..utils import jsonld_use_cache, make_string_from_bytes, MESSAGE_LEVEL_ERROR
from ..tasks.task_types import DETECT_INPUT_TYPE, FETCH_HTTP_NODE, PROCESS_JWS_INPUT
from .utils import abbreviate_value as abv, task_result


"""
Helpful utils
"""

def input_is_json(user_input):
    try:
        value = json.loads(make_string_from_bytes(user_input))
        return True
    except (ValueError, TypeError):
        return False


def input_is_jws(user_input):
    jws_regex = re.compile(r'^[A-z0-9\-=]+.[A-z0-9\-=]+.[A-z0-9\-_=]+$')
    return bool(jws_regex.match(make_string_from_bytes(user_input)))


def find_id_in_jsonld(json_string, jsonld_options):
    input_data = json.loads(json_string)
    result = jsonld.compact(input_data, OPENBADGES_CONTEXT_V2_URI, options=jsonld_options)
    node_id = result.get('id','')
    return node_id


def find_1_0_verify_url(json_string, options):
    input_data = json.loads(json_string)
    try:
        return input_data['verify']['url']
    except KeyError:
        return ''

"""
Input-processing tasks
"""
def detect_input_type(state, task_meta, **options):
    """
    Detects what data format user has provided and saves to the store.
    """
    input_value = state.get('input').get('value')
    depth = task_meta.get('depth')
    detected_type = None
    new_actions = []

    if is_url(input_value):
        detected_type = 'url'
        new_actions.append(set_input_type(detected_type))
        new_actions.append(add_task(
            FETCH_HTTP_NODE, url=input_value, is_potential_baked_input=task_meta.get('is_potential_baked_input', True), depth=depth
        ))
        new_actions.append(set_validation_subject(input_value))
    elif input_is_json(input_value):
        for url_finder in [find_id_in_jsonld, find_1_0_verify_url]:
            id_url = url_finder(input_value, options.get('jsonld_options', jsonld_use_cache))
            if is_url(id_url):
                detected_type = 'url'
                new_actions.append(store_input(id_url))
                break
            else:
                detected_type = 'json'

        new_actions.append(set_input_type(detected_type))
        if detected_type == 'json':
            new_actions.append(report_message(
                'Could not determine verifiable input from provided JSON. No hosted verification URL found.',
                message_level=MESSAGE_LEVEL_ERROR
            ))
        elif detected_type == 'url':
            new_actions.append(add_task(FETCH_HTTP_NODE, url=id_url, is_potential_baked_input=False, depth=depth))
            new_actions.append(set_validation_subject(id_url))
    elif input_is_jws(input_value):
        detected_type = 'jws'
        new_actions.append(set_input_type(detected_type))
        new_actions.append(add_task(PROCESS_JWS_INPUT, data=input_value, depth=depth))
    else:
        raise NotImplementedError("only URL, JSON, or JWS input implemented so far")

    return task_result(
        message="Input of type {} detected.".format(detected_type),
        actions=new_actions
    )


def process_baked_resource(state, task_meta, **options):
    try:
        node_id = task_meta['node_id']
        resource_b64 = state['input']['original_json'][node_id]
        depth = task_meta['depth']
    except KeyError:
        raise TaskPrerequisitesError()
    try:
        search_string = resource_b64.decode('utf-8')
        match = re.search(r'^data:(image\/png|image\/svg\+xml);base64,(.+)$', search_string)
        content_type = match.group(1)
        suffix = '.png' if content_type == 'image/png' else '.svg'
        b64_data = match.group(2)
    except (AttributeError, IndexError):
        return task_result(False, "Cannot determine image type or content from dataURI {}".format(abv(resource_b64)))

    baked_file = NamedTemporaryFile(suffix=suffix)
    baked_file.write(base64.b64decode(b64_data))
    baked_file.seek(0)

    assertion_data = unbake(baked_file)

    if assertion_data:
        actions = [
            store_input(assertion_data),
            add_task(DETECT_INPUT_TYPE, is_potential_baked_input=False, depth=depth)
        ]
        return task_result(True, "Retrieved baked data from image resource {}".format(abv(node_id)), actions)
    else:
        return task_result(
            False, "Resource {} was an image of known type but no baked Open Badges data was available".format(
                abv(node_id)
            ))
