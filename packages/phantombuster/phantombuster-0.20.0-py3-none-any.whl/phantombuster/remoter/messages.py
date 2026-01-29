from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, NoReturn, Optional, Set, Union, cast
from types import TracebackType
import pickle
import base64

try:
    from typing import Literal
except:

    class MyLiteral:
        def __init__(self, t):
            self.t = t

        def __getitem__(self, *args, **kwargs):
            return self.t

    Literal = MyLiteral(str)  # type: ignore


class RemoterException(Exception):
    pass


## ==== Messages ====
#
# All Messages that can be exchanged by workers and the server


@dataclass
class FreeMsg:
    """Indicates the worker is free for more work"""

    name: str


@dataclass
class OKMsg:
    """Indicates the requested action succeeded

    Used as answer for Lock, Result and Store messages."""

    pass


@dataclass
class FailMsg:
    """Indicates the requested action failed terminally

    Used as answer for Lock, Result and Store messages."""

    name: str
    message: str


@dataclass
class QueryMsg:
    """Query properties of the server like number of workers or tasks"""

    property: str


@dataclass
class QueryAnswerMsg:
    """Answer for a query"""

    property: str


@dataclass
class TaskMsg:
    """Indicates a task to be executed by the worker"""

    name: str
    persister: str
    task_hash: str
    datetime: datetime
    function_module: str
    function_name: str
    function_hash: str
    kwargs: Dict[str, Any]
    failed: bool
    exception: Optional[tuple[BaseException, TracebackType]]
    request: bool
    time: Optional[float]

@dataclass
class FSaveMsg:
    """Saving a function"""
    datetime: datetime
    function_module: str
    function_name: str
    function_hash: str
    function_code: str

@dataclass
class ResultMsg:
    """Indicates the result of the assigned task.

    outdated, currently `Store`s communicate via StoreMsgs"""

    task_hash: str
    datetime: datetime
    function_name: str
    function_module: str
    kwargs: Dict[str, Any]
    worker_name: str
    result: Any = None


@dataclass
class WaitMsg:
    """Indicate the worker that no work is available, but more might follow

    Is used as an answer to a `FreeMsg` or to a `LockMsg`"""

    time: int


@dataclass
class QuitMsg:
    """Indicate the worker to shut down

    is used as an answer to a `FreeMsg`"""

    name: str
    client_type: str

@dataclass
class LockMsg:
    """Asks to acquire a lock"""

    operation: Literal["lock", "unlock"]
    lock: str
    name: str


@dataclass
class LoadMsg:
    """Asks to load multiple tasks"""
    task_hashs: List[str]


@dataclass
class StoreMsg:
    """Updates a Store"""

    datetime: datetime
    function_module: str
    function_name: str
    function_hash: str
    kwargs: Dict[str, Any]
    result: Union[Any, bytes]
    task_hash: str
    result_type: str
    failed: bool
    time: float

    def __repr__(self):
        kwargs = str(self.kwargs)
        if len(kwargs) > 20:
            kwargs = kwargs[:10] + "..." + kwargs[-10:]

        return f"StoreMsg(datetime={self.datetime}, function_module={self.function_module}, function_name={self.function_name}, function_hash={self.function_hash}, kwargs={kwargs}, result=..., task_hash={self.task_hash}, result_type={self.result_type}, failed={self.failed}, time={self.time})"


    def __str__(self):
        kwargs = str(self.kwargs)
        if len(kwargs) > 20:
            kwargs = kwargs[:10] + "..." + kwargs[-10:]

        return f"StoreMsg(datetime={self.datetime}, function_module={self.function_module}, function_name={self.function_name}, function_hash={self.function_hash}, kwargs={kwargs}, result=..., task_hash={self.task_hash}, result_type={self.result_type}, failed={self.failed}, time={self.time})"



@dataclass
class ExceptionMsg:
    name: str
    exception: str

@dataclass
class JoinMsg:
    name: str
    client_type: str

# Typing Stuff to make sure all messages are always handled in all code paths

Message     =          Union[QueryMsg, QueryAnswerMsg, OKMsg , FreeMsg, TaskMsg, QuitMsg, LockMsg, LoadMsg, WaitMsg, ResultMsg, StoreMsg, FailMsg, ExceptionMsg, JoinMsg, FSaveMsg]

# A serialized message indicates its type by a token, this lists the available tokens.
# Order is the same as the Message Type
MessageType =               ["QUERY", "ANSWER", "OKOK" , "FREE" ,  "TASK", "QUIT",  "LOCK",  "WAIT",  "RESULT",  "STORE",  "FAIL", "EXCEPTION", "JOIN", "FSAVE", "LOAD"]
# Type of MesssageType, used when only the tokens listed in MessageType are accectable
MessageTypeLiteral = Literal["QUERY", "ANSWER", "OKOK" , "FREE" ,  "TASK", "QUIT",  "LOCK",  "WAIT",  "RESULT",  "STORE",  "FAIL", "EXCEPTION", "JOIN", "FSAVE", "LOAD"]

# Can be used to enable exhaustive type checking in mypy, see https://hakibenita.com/python-mypy-exhaustive-checking
def assert_never(x: NoReturn) -> NoReturn:
    raise Exception("This should never happen.")
