from ctypes import (
    c_int,
    c_uint,
    c_ulonglong,
    c_char_p,
    c_void_p,
    Structure,
    CDLL,
    POINTER,
    string_at
)
import json
from typing import Optional
from pathlib import Path
import platform

from .models import GetChatDataResponse, GetMediaDataResponse
from .error import WeWorkFinanceError
from .logger import logger


class Slice(Structure):
    _fields_ = [
        ("buf", c_char_p),
        ("len", c_int),
    ]


class MediaData(Structure):
    _fields_ = [
        ("outindexbuf", c_char_p),
        ("out_len", c_int),
        ("data", c_char_p),
        ("data_len", c_int),
        ("is_finish", c_int),
    ]


class WeWorkFinance:
    def __init__(
        self,
        corpid: str,
        secret: str,
        dll_path: Optional[str] = None,
        default_timeout: int = 5,
    ):
        logger.info("初始化WeWorkFinanceSDK")
        logger.debug(f"{corpid=}")
        logger.debug(f"{secret=}")
        logger.debug(f"{dll_path=}")
        self._lib = self._load_library(dll_path)
        self._setup_signatures()
        self._sdk = self._lib.NewSdk()
        ret = self._lib.Init(self._sdk, corpid.encode("utf-8"), secret.encode("utf-8"))
        self.default_timeout = default_timeout
        if ret != 0:
            raise WeWorkFinanceError(ret, f"初始化失败: {ret}")

    def _load_library(self, dll_path: Optional[str]) -> CDLL:
        path = None
        if dll_path:
            path = Path(dll_path)
            if not path.exists():
                raise FileNotFoundError(f"找不到自定义DLL路径: {dll_path}")
        else:
            base_dir = Path(__file__).parent.absolute()
            system = platform.system()
            machine = platform.machine()
            # 确定平台和内置库路径
            if system == "Windows":
                if machine == "AMD64" or machine == "x86_64":
                    lib_dir = Path(base_dir, "libs", "windows")
                    lib_filename = "WeWorkFinanceSdk.dll"
                else:
                    raise OSError(f"不支持的CPU架构: {machine}")
            elif system == "Linux":
                if machine == "AMD64" or machine == "x86_64":
                    lib_dir = Path(base_dir, "libs", "linux")
                    lib_filename = "libWeWorkFinanceSdk_C_x86.so"
                elif machine == "arm64" or machine == "aarch64":
                    lib_dir = Path(base_dir, "libs", "linux")
                    lib_filename = "libWeWorkFinanceSdk_C_arm.so"
                else:
                    raise OSError(f"不支持的CPU架构: {machine}")
            elif system == "Darwin":
                raise OSError(f"不支持MACOS操作系统,可以在Docker中的Linux运行")
            else:
                raise OSError(f"不支持的操作系统: {system}")
            path = Path(lib_dir, lib_filename)
            if not path.exists():
                raise FileNotFoundError(f"未找到内置SDK库文件，路径: {path}")
        logger.debug(f"加载DLL: {path}")
        try:
            lib = CDLL(str(path.resolve()))
            return lib
        except Exception as e:
            raise WeWorkFinanceError(-1, f"加载DLL失败 {str(path)}: {e}")

    def _setup_signatures(self):
        # NewSdk
        self._lib.NewSdk.restype = c_void_p

        # Init
        self._lib.Init.argtypes = [c_void_p, c_char_p, c_char_p]
        self._lib.Init.restype = c_int

        # GetChatData
        self._lib.GetChatData.argtypes = [
            c_void_p,
            c_ulonglong,
            c_uint,
            c_char_p,
            c_char_p,
            c_int,
            POINTER(Slice),
        ]
        self._lib.GetChatData.restype = c_int

        # DecryptData
        self._lib.DecryptData.argtypes = [c_char_p, c_char_p, POINTER(Slice)]
        self._lib.DecryptData.restype = c_int

        # GetMediaData
        self._lib.GetMediaData.argtypes = [
            c_void_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_int,
            POINTER(MediaData),
        ]
        self._lib.GetMediaData.restype = c_int

        # DestroySdk
        self._lib.DestroySdk.argtypes = [c_void_p]
        self._lib.DestroySdk.restype = None

        # Slice utilities
        self._lib.NewSlice.restype = POINTER(Slice)
        self._lib.FreeSlice.argtypes = [POINTER(Slice)]
        self._lib.GetContentFromSlice.argtypes = [POINTER(Slice)]
        self._lib.GetContentFromSlice.restype = c_char_p
        self._lib.GetSliceLen.argtypes = [POINTER(Slice)]
        self._lib.GetSliceLen.restype = c_int

        # MediaData utilities
        self._lib.NewMediaData.restype = POINTER(MediaData)
        self._lib.FreeMediaData.argtypes = [POINTER(MediaData)]
        self._lib.GetOutIndexBuf.argtypes = [POINTER(MediaData)]
        self._lib.GetOutIndexBuf.restype = c_char_p
        self._lib.GetData.argtypes = [POINTER(MediaData)]
        self._lib.GetData.restype = c_void_p
        self._lib.GetIndexLen.argtypes = [POINTER(MediaData)]
        self._lib.GetIndexLen.restype = c_int
        self._lib.GetDataLen.argtypes = [POINTER(MediaData)]
        self._lib.GetDataLen.restype = c_int
        self._lib.IsMediaDataFinish.argtypes = [POINTER(MediaData)]
        self._lib.IsMediaDataFinish.restype = c_int

    def _destroy(self):
        if self._sdk:
            self._lib.DestroySdk(self._sdk)
            self._sdk = None

    def __del__(self):
        self._destroy()

    def get_chat_data(
        self,
        seq: int = 0,
        limit: int = 1000,
        proxy: str = "",
        passwd: str = "",
        timeout: int = 0,
    ) -> GetChatDataResponse:
        if timeout == 0:
            timeout = self.default_timeout
        logger.info("拉取聊天记录")
        logger.debug(f"{seq=}")
        logger.debug(f"{limit=}")
        logger.debug(f"{proxy=}")
        logger.debug(f"{passwd=}")
        logger.debug(f"{timeout=}")
        slice_obj = self._lib.NewSlice()
        try:
            ret = self._lib.GetChatData(
                self._sdk,
                c_ulonglong(seq),
                c_uint(limit),
                proxy.encode("utf-8"),
                passwd.encode("utf-8"),
                c_int(timeout),
                slice_obj,
            )
            logger.debug(f"{ret=}")
            data = b""
            if ret != 0:
                raise WeWorkFinanceError(ret, "拉取聊天记录失败")
            content = self._lib.GetContentFromSlice(slice_obj)
            logger.debug(f"{content=}")
            data = GetChatDataResponse.from_json(content)
            if data.errcode != 0:
                raise WeWorkFinanceError(data.errcode, data.errmsg)
            return data
        finally:
            if slice_obj:
                self._lib.FreeSlice(slice_obj)

    def decrypt_data(self, encrypt_key: str, encrypt_msg: str):
        logger.info("解密消息")
        logger.debug(f"{encrypt_key=}")
        logger.debug(f"{encrypt_msg=}")
        slice_obj = self._lib.NewSlice()
        try:
            ret = self._lib.DecryptData(
                encrypt_key.encode("utf-8"), encrypt_msg.encode("utf-8"), slice_obj
            )
            if ret != 0:
                logger.debug(f"{ret=}")
                raise WeWorkFinanceError(ret, "解密聊天消息失败")
            data = json.loads(self._lib.GetContentFromSlice(slice_obj))
            logger.debug(f"{data=}")
            return data
        finally:
            if slice_obj:
                self._lib.FreeSlice(slice_obj)

    # GetMediaData
    def get_media_data(
        self,
        sdk_fileid: str,
        index_buf: Optional[str] = None,
        proxy: str = "",
        passwd: str = "",
        timeout: int = 0,
    ) -> GetMediaDataResponse:
        if timeout == 0:
            timeout = self.default_timeout
        logger.info("下载媒体文件")
        logger.debug(f"{sdk_fileid=}")
        logger.debug(f"{index_buf=}")
        logger.debug(f"{proxy=}")
        logger.debug(f"{passwd=}")
        logger.debug(f"{timeout=}")

        media_data = self._lib.NewMediaData()
        try:
            ret = self._lib.GetMediaData(
                self._sdk,
                index_buf.encode("utf-8") if index_buf else None,
                sdk_fileid.encode("utf-8"),
                proxy.encode("utf-8"),
                passwd.encode("utf-8"),
                c_int(timeout),
                media_data,
            )
            if ret != 0:
                logger.debug(f"{ret=}")
                raise WeWorkFinanceError(ret, "下载媒体文件失败")
            data_ptr = self._lib.GetData(media_data)
            data_len = self._lib.GetDataLen(media_data)
            data = string_at(data_ptr, data_len)
            outindexbuf = self._lib.GetOutIndexBuf(media_data).decode("utf-8")
            is_finish = self._lib.IsMediaDataFinish(media_data)
            return GetMediaDataResponse(
                data=data,
                outindexbuf=outindexbuf,
                is_finish=is_finish,
            )
        finally:
            if media_data:
                self._lib.FreeMediaData(media_data)
