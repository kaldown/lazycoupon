# TODO: with no ack
# TODO: decorator to catch exceptions => to bypass some logic
# TODO: separate read at the start of event from write from an event end


import logging
import time
from functools import wraps

import requests

import settings
from utils import push_event

logging.getLogger().setLevel(logging.INFO)


_STATES = [
    'init',
    'set_provider',
    'get_phone',
    'set_phone',
    'get_code',
    'set_code',
    'chose_seller',
    'quit',
]


def _next_state(state):
    return _STATES[_STATES.index(state) + 1]


def event(func):
    @wraps(func)
    def handle_event(obj):
        counter = 0
        func_name = func.__name__
        while counter < settings.MAX_RETRY:
            try:
                func(obj)
            except Retry:
                logging.error('retrying %s with %s', func_name, obj)
                time.sleep(2)
            else:
                break
            finally:
                counter += 1
        else:
            # fail
            push_event('quit', obj)
            return

        # success
        next_func_name = _next_state(func_name)
        push_event(next_func_name, obj)

    return handle_event


PROVIDER_URI_MAP = {
    # https://smska.net/?mode=info&ul=api
    'smska.net': 'https://smska.net/stubs/handler_api.php?api_key={api_key}'.format(
        api_key=settings.API_KEY_SMSKA_NET)
}


@event
def init(obj):
    return


def quit(obj):
    logging.info('u r done')
    # commit results to db
    if settings.DEVMODE:
        exit(0)


@event
def set_provider(obj):
    obj['service'] = 'ye'
    obj['provider'] = 'smska.net'
    return


@event
def get_phone(obj):
    id, phone = _get_id_phone(obj)
    _prepare_id_phone(obj, id, phone)
    # TODO: ack when front phone is set


def _get_id_phone(obj):
    service = obj['service']
    forward = 0
    operator = 'any'
    provider = obj['provider']

    url = ''.join([PROVIDER_URI_MAP[provider],
                   f'&action=getNumber&service={service}&forward={forward}&operator={operator}'])
    id = phone = None
    res = requests.get(url)
    id, phone = _check_phone(res.text)
    return id, phone


def _prepare_id_phone(obj, id, phone):
    obj['provider_id'] = id
    obj['provider_phone'] = phone


def _check_phone(text):
    """
    Success:
        ACCESS_NUMBER:$id:$number

    Failure:
        NO_NUMBERS
        NO_BALANCE
        BAD_ACTION
        BAD_SERVICE
        BAD_KEY
        ERROR_SQL
    """
    logging.info('[phone] %s', text)
    status = text.split(':')
    if status[0] == 'ACCESS_NUMBER':
        return status[1], status[2]
    raise Retry


@event
def get_code(obj):
    provider = obj['provider']
    id = obj['provider_id']

    url = ''.join([PROVIDER_URI_MAP[provider],
                   f'&action=getStatus&id={id}'])
    code = None
    while code is None:
        time.sleep(5)
        res = requests.get(url)
        code = _check_code(res)

    obj['provider_code'] = code
    return


def _check_code(res):
    text = res.text
    logging.info('[code] %s', text)
    status, *tail = text.split(':')
    if status == 'STATUS_OK':
        return tail[0]
    return None


FUNCTIONS = {
    'init': init,
    'set_provider': set_provider,
    'get_phone': get_phone,
    'get_code': get_code,
    'quit': quit,
}


class Retry(Exception):
    pass
