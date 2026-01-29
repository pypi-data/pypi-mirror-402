from typing import Optional
from typing import Any, Callable, Dict, List, NoReturn, Optional, Set, Union, cast
from types import TracebackType
from datetime import datetime
from phantombuster.config_files import InputFile, RegexDictionary, InputGroup
from phantombuster.remoter.messages import Message, FreeMsg, OKMsg, FailMsg, QueryMsg, QueryAnswerMsg, TaskMsg, FSaveMsg, ResultMsg, WaitMsg, QuitMsg, LockMsg, LoadMsg, StoreMsg, ExceptionMsg, JoinMsg, MessageType, MessageTypeLiteral

import pickle
import json
import base64

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

def error_to_string(err: Optional[tuple[BaseException, TracebackType]]) -> Optional[str]:
    if err:
        return str(err)
        #return pickle.dumps(err, protocol=pickle.HIGHEST_PROTOCOL).decode("utf8", "surrogateescape")
    return None

def string_to_error(s: Optional[str]) -> Optional[tuple[BaseException, TracebackType]]:
    if s:
        return s, None
        return pickle.loads(s.encode("utf8", "surrogateescape"))
    return None

EXTENSIONS = {}

def register_serialisation(cls):
    EXTENSIONS[cls.__name__] = cls
    return cls

def register_serialization_extension(name, cls):
    EXTENSIONS[name] = cls

register_serialization_extension('InputFile', InputFile)
register_serialization_extension('RegexDictionary', RegexDictionary)
register_serialization_extension('InputGroup', InputGroup)

def serialize_value(value):
    if isinstance(value, Task):
        value.calc_hash()
        return ('t', value.task_hash)
    if isinstance(value, list):
        return ('l', [serialize_value(v) for v in value])
    if isinstance(value, dict):
        return ('d', {key: serialize_value(v) for key, v in value.items()})

    for name, cls in EXTENSIONS.items():
        if isinstance(value, cls):
            return ('e', {'name': name, 'value': value._to_json_e()})
    return ('a', value)

def deserialize_value(value, store):
    value_type, value = value
    if value_type == 't':
        task = store.load_from_hash(value)
        if task is None:
            raise Exception(f'Could not deserialize task with hash {value["value"]}')
        return task
    elif value_type == 'l':
        return [deserialize_value(v, store) for v in value]
    elif value_type == 'd':
        return {key: deserialize_value(v, store) for key, v in value.items()}
    elif value_type == 'e':
        cls = EXTENSIONS[value['name']]
        return cls._from_json_e(value['value'])
    elif value_type == 'a':
        return value

def serialize_kwargs(kwargs):
    if kwargs is not None:
        kwargs = {key: serialize_value(value) for key, value in kwargs.items()}
        kwargs = _clean(kwargs)
    return json.dumps(kwargs)

def deserialize_kwargs(string, store):
    kwargs = json.loads(string)
    if kwargs is not None:
        kwargs = {key: deserialize_value(value, store) for key, value in kwargs.items()}
    return kwargs

def _clean(v):
    if isinstance(v, dict):
        r = {}
        for key in sorted(v):
            r[key] = _clean(v[key])
        return r
    return v


# ==== De/Serializing Messages ====


def parse_json_to_message(j: Dict[str, Any], store: 'Store') -> Message:
    """Deserialize a json-like dict to a message"""
    if "type" not in j:
        raise Exception("Message had no declared type.")
    t: MessageTypeLiteral = j["type"]
    if t not in MessageType:
        raise Exception(f"Unknown type {t}")
    if t == "FREE":
        if "name" not in j:
            raise Exception("Free message does not contain worker name")
        return FreeMsg(j["name"])
    elif t == "OKOK":
        return OKMsg()
    elif t == "QUERY":
        return QueryMsg(j["property"])
    elif t == "ANSWER":
        return QueryAnswerMsg(j["property"])
    elif t == "FSAVE":
        return FSaveMsg(
            datetime=datetime.strptime(j["datetime"], DATETIME_FORMAT) if j['datetime'] else None,
            function_module=j["function_module"],
            function_name=j["function_name"],
            function_hash=j["function_hash"],
            function_code=j["function_code"],
        )
    elif t == "TASK":
        return TaskMsg(
            name=j['name'],
            persister=j["persister"],
            task_hash=j["task_hash"],
            datetime=datetime.strptime(j["datetime"], DATETIME_FORMAT) if j['datetime'] else None,
            function_module=j["function_module"],
            function_name=j["function_name"],
            function_hash=j["function_hash"],
            kwargs=deserialize_kwargs(j["kwargs"], store),
            failed=j["failed"],
            exception=string_to_error(j["exception"]),
            request=j["request"],
            time=j["time"]
        )
    elif t == "QUIT":
        return QuitMsg(name=j["name"], client_type=j["client_type"])
    elif t == "LOCK":
        return LockMsg(operation=j["op"], lock=j["lock"], name=j["name"])
    elif t == "LOAD":
        return LoadMsg(task_hashs=j["task_hashs"])
    elif t == "WAIT":
        return WaitMsg(j["time"])
    elif t == "RESULT":
        return ResultMsg(
            task_hash=j["task_hash"],
            datetime=datetime.strptime(j["datetime"], DATETIME_FORMAT),
            function_module=j["function_module"],
            function_name=j["function_name"],
            kwargs=deserialize_kwargs(j["kwargs"], store),
            worker_name=j["worker_name"],
            result=j["result"],
        )
    elif t == "STORE":
        r = pickle.loads(base64.b64decode(j["result"].encode("utf-8")))
        return StoreMsg(
            datetime=datetime.strptime(j["datetime"], DATETIME_FORMAT),
            function_module=j["function_module"],
            function_name=j["function_name"],
            function_hash=j["function_hash"],
            kwargs=deserialize_kwargs(j["kwargs"], store),
            result=r,
            task_hash=j["task_hash"],
            result_type=j["result_type"],
            failed=j["failed"],
            time=j["time"],
        )
    elif t == "FAIL":
        return FailMsg(name=j["name"], message=j["message"])
    elif t == "EXCEPTION":
        return ExceptionMsg(name=j["name"], exception=j["exception"])
    elif t == "JOIN":
        return JoinMsg(name=j["name"], client_type=j["client_type"])
    else:
        assert_never(t)


def message_to_json(msg: Message) -> Dict[str, Any]:
    """Serialize a message to json-like dict"""
    if isinstance(msg, OKMsg):
        return {"type": "OKOK"}
    elif isinstance(msg, QueryMsg):
        return {"type": "QUERY", "property": msg.property}
    elif isinstance(msg, QueryAnswerMsg):
        return {"type": "ANSWER", "property": msg.property}
    elif isinstance(msg, FreeMsg):
        return {"type": "FREE", "name": msg.name}
    elif isinstance(msg, TaskMsg):
        return {
            "type": "TASK",
            "name": msg.name,
            "persister": msg.persister,
            "task_hash": msg.task_hash,
            "datetime": msg.datetime.strftime(DATETIME_FORMAT) if msg.datetime else None,
            "function_module": msg.function_module,
            "function_name": msg.function_name,
            "function_hash": msg.function_hash,
            "kwargs": serialize_kwargs(msg.kwargs),
            "failed": msg.failed,
            "exception": error_to_string(msg.exception),
            "request": msg.request,
            "time": msg.time
        }
    elif isinstance(msg, FSaveMsg):
        return {
            "type": "FSAVE",
            "datetime": msg.datetime.strftime(DATETIME_FORMAT) if msg.datetime else None,
            "function_module": msg.function_module,
            "function_name": msg.function_name,
            "function_hash": msg.function_hash,
            "function_code": msg.function_code,
        }
    elif isinstance(msg, QuitMsg):
        return {"type": "QUIT", "name": msg.name, "client_type": msg.client_type}
    elif isinstance(msg, LockMsg):
        return {"type": "LOCK", "op": msg.operation, "name": msg.name, "lock": msg.lock}
    elif isinstance(msg, LoadMsg):
        return {"type": "LOAD", "task_hashs": msg.task_hashs}
    elif isinstance(msg, WaitMsg):
        return {"type": "WAIT", "time": msg.time}
    elif isinstance(msg, ResultMsg):
        return {
            "type": "RESULT",
            "task_hash": msg.task_hash,
            "datetime": msg.datetime.strftime(DATETIME_FORMAT),
            "function_module": msg.function_module,
            "function_name": msg.function_name,
            "kwargs": serialize_kwargs(msg.kwargs),
            "worker_name": msg.worker_name,
            "result": msg.result,
        }
    elif isinstance(msg, StoreMsg):
        r = base64.b64encode(pickle.dumps(msg.result)).decode("utf-8")
        msg = {
            "datetime": msg.datetime.strftime(DATETIME_FORMAT),
            "type": "STORE",
            "function_module": msg.function_module,
            "function_name": msg.function_name,
            "function_hash": msg.function_hash,
            "kwargs": serialize_kwargs(msg.kwargs),
            "result": r,
            "task_hash": msg.task_hash,
            "result_type": msg.result_type,
            "failed": msg.failed,
            "time": msg.time,
        }
        return msg
    elif isinstance(msg, FailMsg):
        return {"type": "FAIL", "name": msg.name, "message": msg.message}
    elif isinstance(msg, ExceptionMsg):
        return {"type": "EXCEPTION", "name": msg.name, "exception": msg.exception}
    elif isinstance(msg, JoinMsg):
        return {"type": "JOIN", "name": msg.name, "client_type": msg.client_type}
    else:
        assert_never(msg)

def init_task(task):
    global Task
    Task = task
