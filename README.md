# PyWeWorkFinance

[![PyPI version](https://badge.fury.io/py/pyweworkfinance.svg)](https://badge.fury.io/py/pyweworkfinance)
[![Python Version](https://img.shields.io/pypi/pyversions/pyweworkfinance)](https://pypi.org/project/pyweworkfinance/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python 封装的企业微信会话存档 SDK（WeChat Work Finance SDK）

[GitHub](https://github.com/911061873/PyWeWorkFinance) • [PyPI](https://pypi.org/project/pyweworkfinance/) • [文档](https://github.com/yingdao/PyWeWorkFinance#readme)

## 项目概述

PyWeWorkFinance 是对企业微信官方会话存档 SDK 的 Python 封装，提供了便捷的接口来访问和处理企业微信的聊天记录、媒体文件等数据。

## 主要功能

- **获取聊天记录**：支持按序列号和数量限制拉取加密的聊天数据
- **解密聊天消息**：使用加密密钥解密企业微信发送的聊天消息
- **下载媒体文件**：获取聊天中的图片、视频、文件等媒体数据
- **跨平台支持**：支持 Windows、Linux (x86/ARM) 等多个平台
- **代理支持**：可配置代理服务器和代理密码
- **超时控制**：可设置请求超时时间

## 兼容性

| 平台    | x86_64 | ARM64 |
| ------- | ------ | ----- |
| Windows | ✓      | ✗     |
| Linux   | ✓      | ✓     |
| macOS   | ✗      | ✗     |

macOS 平台不支持,可尝试在 Docker 里运行

### Windows

- 支持 x86_64 (AMD64) 架构
- 库文件：`WeWorkFinanceSdk.dll`

### Linux

- 支持 x86_64 架构，库文件：`libWeWorkFinanceSdk_C_x86.so`
- 支持 ARM64 架构，库文件：`libWeWorkFinanceSdk_C_arm.so`

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install pyweworkfinance
```

## 快速开始

### 初始化 SDK

```python
from pyweworkfinance import WeWorkFinance

# 创建 SDK 实例
sdk = WeWorkFinance(
    corpid="your_corpid",
    secret="your_secret",
    default_timeout=5
)
```

### 获取聊天记录

```python
# 拉取聊天数据
response = sdk.get_chat_data(
    seq=0,           # 起始序列号
    limit=1000,      # 拉取数量限制
    proxy="",        # 代理地址（可选）
    passwd="",       # 代理密码（可选）
    timeout=5        # 超时时间（秒）
)

# 处理响应
if response.errcode == 0:
    for chat in response.chatdata:
        print(f"序列号: {chat.seq}")
        print(f"消息ID: {chat.msgid}")
        print(f"公钥版本: {chat.publickey_ver}")
        print(f"加密随机密钥: {chat.encrypt_random_key}")
        print(f"加密消息: {chat.encrypt_chat_msg}")
else:
    print(f"错误: {response.errmsg}")
```

### 解密聊天消息

**注意：** 解密功能依赖 `pycryptodome`，请先安装：

```bash
pip install pycryptodome
```

```python
# 解密单条消息
from base64 import b64decode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
# 创建私钥对象
private_key = RSA.import_key(open("your_pub.pem", "r").read())
cipher = PKCS1_v1_5.new(private_key)
# 解密随机密钥
random_key = b64decode(chat.encrypt_random_key)
random_key = cipher.decrypt(random_key, None).decode()
# 解密消息
message = sdk.decrypt_data(
    encrypt_key=random_key,
    encrypt_msg=chat.encrypt_chat_msg
)
print(message)
```

### 下载媒体文件

```python
# 首次下载
response = sdk.get_media_data(
    sdk_fileid="file_id_from_chat_msg",
    index_buf=None,  # 首次为 None，后续使用返回的 outindexbuf
    timeout=5
)

# 处理分片数据
media_data = response.data

# 检查是否已完成
if response.is_finish:
    print("媒体文件下载完成")
else:
    # 继续下载下一分片
    next_response = sdk.get_media_data(
        sdk_fileid="file_id",
        index_buf=response.outindexbuf,  # 使用上一次返回的索引
        timeout=5
    )
```

## 高级用法

### 自定义库文件路径

如果需要使用自定义的 SDK 库文件：

```python
sdk = WeWorkFinance(
    corpid="your_corpid",
    secret="your_secret",
    dll_path="/path/to/custom/sdk.dll"
)
```

### 分片下载大文件

```python
all_data = b""
index_buf = None

while True:
    response = sdk.get_media_data(
        sdk_fileid="file_id",
        index_buf=index_buf,
        timeout=10
    )

    all_data += response.data
    index_buf = response.outindexbuf

    if response.is_finish:
        break

# all_data 包含完整的文件数据
```

## 作者

yunchuan@yingdao

## 常见问题

### Q: 如何获取 corpid 和 secret?

A: 需要在企业微信管理后台的应用管理中创建应用，获取应用的 ID 和密钥。

### Q: 库文件找不到？

A: 确保：

- 项目已正确安装
- SDK 库文件位于正确的 libs 目录
- 操作系统和 CPU 架构与库文件匹配

### Q: 解密失败？

A: 检查：

- encrypt_key 和 encrypt_msg 是否正确
- 企业微信账号的私钥配置是否正确

### Q: 支持 macOS 吗？

A: 当前不支持 macOS，可在 Docker 中的 Linux 环境中运行。
