import json
import logging

import redis


logging.getLogger().setLevel(logging.INFO)


STORAGE = redis.Redis(host='localhost', port=6379, db=0)
EXPIRE = 20 * 60

TASK_CHANNEL = 'TASK_CHANNEL'


def order_save(id, obj):
    STORAGE.set(id, obj)


def order_get(id):
    return STORAGE.get(id)


def push_event(func_name, obj):
    message = {
        'func_name': func_name,
        'arguments': obj,
    }
    STORAGE.publish(TASK_CHANNEL, json.dumps(message).encode())
    logging.info('spawning %s', message)
