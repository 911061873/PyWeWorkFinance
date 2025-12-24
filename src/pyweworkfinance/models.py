from dataclasses import dataclass
import json


@dataclass
class EncryptChatData:
    seq: int
    msgid: str
    publickey_ver: int
    encrypt_random_key: str
    encrypt_chat_msg: str


@dataclass
class GetChatDataResponse:
    errcode: int
    errmsg: str
    chatdata: list[EncryptChatData]

    @classmethod
    def from_json(cls, json_str: str | bytes) -> "GetChatDataResponse":
        data = json.loads(json_str)
        chatdatas = data.pop("chatdata", [])
        chatdatas = [EncryptChatData(**item) for item in chatdatas]
        return cls(**data, chatdata=chatdatas)


@dataclass
class GetMediaDataResponse:
    data: bytes
    outindexbuf: str
    is_finish: bool
