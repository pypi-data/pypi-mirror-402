from buf.validate import validate_pb2 as _validate_pb2
from meshtrade.option.method_options.v1 import method_options_pb2 as _method_options_pb2
from meshtrade.testing.ledger.token_tap.v1 import option_pb2 as _option_pb2
from meshtrade.type.v1 import amount_pb2 as _amount_pb2
from meshtrade.type.v1 import token_pb2 as _token_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class InitialiseTokenTapsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class InitialiseTokenTapsResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListTokenTapsRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ListTokenTapsResponse(_message.Message):
    __slots__ = ("tokens",)
    TOKENS_FIELD_NUMBER: _ClassVar[int]
    tokens: _containers.RepeatedCompositeFieldContainer[_token_pb2.Token]
    def __init__(self, tokens: _Optional[_Iterable[_Union[_token_pb2.Token, _Mapping]]] = ...) -> None: ...

class MintTokenRequest(_message.Message):
    __slots__ = ("amount", "address", "options")
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    amount: _amount_pb2.Amount
    address: str
    options: _option_pb2.MintTokenOptions
    def __init__(self, amount: _Optional[_Union[_amount_pb2.Amount, _Mapping]] = ..., address: _Optional[str] = ..., options: _Optional[_Union[_option_pb2.MintTokenOptions, _Mapping]] = ...) -> None: ...

class MintTokenResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
