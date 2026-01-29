import json

import jsonpickle


def toJSON(object) -> str:
    return json.loads(jsonpickle.encode(object, unpicklable=False))