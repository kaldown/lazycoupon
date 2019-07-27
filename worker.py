import logging
from operator import itemgetter
import json
import time

from utils import STORAGE, TASK_CHANNEL
from back import FUNCTIONS
import settings


logging.getLogger().setLevel(logging.INFO)


sub = STORAGE.pubsub()
sub.subscribe(TASK_CHANNEL)


def get_message(message):
    """{
        'pattern': None,
        'type': 'subscribe',
        'channel': 'my-second-channel',
        'data': 1L,
    }"""
    if not message:
        return

    logging.info('MSG: %s', message)
    data = message.get('data', {})
    return json.loads(data)


def execute(data):
    if not data:
        return None, None

    try:
        func_name, arguments = itemgetter('func_name', 'arguments')(data)
    except KeyError as exc:
        logging.error('[worker] error %s', exc)
        return

    logging.info('executing: %s, with args: %s', func_name, arguments)
    func = FUNCTIONS.get(func_name)
    if func:
        func(arguments)
    return

def __warmup():
    # warmup
    time.sleep(15)  # settling browser
    sub.get_message()
    STORAGE.publish('TASK_CHANNEL', b'{"func_name": "init", "arguments": {}}')


def process():
    __warmup()

    while True:
        logging.info('tik')
        data = get_message(sub.get_message())
        if data:
            execute(data)
        time.sleep(1)


def main():
    process()


if __name__ == '__main__':
    main()
