from .logger import logger


class WeWorkFinanceError(Exception):
    ERR_MSG_MAP = {
        10000: "参数错误，请求参数错误",
        10001: "网络错误，网络请求错误",
        10002: "数据解析失败",
        10003: "系统失败",
        10004: "密钥错误导致加密失败",
        10005: "fileid错误",
        10006: "解密失败",
        10007: "找不到消息加密版本的私钥，需要重新传入私钥对",
        10008: "解析encrypt_key出错",
        10009: "ip非法",
        10010: "数据过期",
        10011: "证书错误",
    }

    def __init__(self, err_code: int, err_msg: str = ""):
        self.err_code = err_code
        if not err_msg:
            self.err_msg = self.ERR_MSG_MAP.get(err_code, "未知错误")
        else:
            self.err_msg = err_msg
        logger.error(f"企业微信会话存档错误 {err_code}: {self.err_msg}")
        super().__init__(f"企业微信会话存档错误 {err_code}: {self.err_msg}")
