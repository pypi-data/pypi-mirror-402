from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MintTokenOptions(_message.Message):
    __slots__ = ("stellar_mint_options",)
    STELLAR_MINT_OPTIONS_FIELD_NUMBER: _ClassVar[int]
    stellar_mint_options: StellarMintOptions
    def __init__(self, stellar_mint_options: _Optional[_Union[StellarMintOptions, _Mapping]] = ...) -> None: ...

class StellarMintOptions(_message.Message):
    __slots__ = ("options",)
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    options: _containers.RepeatedCompositeFieldContainer[StellarMintOption]
    def __init__(self, options: _Optional[_Iterable[_Union[StellarMintOption, _Mapping]]] = ...) -> None: ...

class StellarMintOption(_message.Message):
    __slots__ = ("stellar_mint_token_with_memo",)
    STELLAR_MINT_TOKEN_WITH_MEMO_FIELD_NUMBER: _ClassVar[int]
    stellar_mint_token_with_memo: StellarMintTokenWithMemo
    def __init__(self, stellar_mint_token_with_memo: _Optional[_Union[StellarMintTokenWithMemo, _Mapping]] = ...) -> None: ...

class StellarMintTokenWithMemo(_message.Message):
    __slots__ = ("memo",)
    MEMO_FIELD_NUMBER: _ClassVar[int]
    memo: str
    def __init__(self, memo: _Optional[str] = ...) -> None: ...
