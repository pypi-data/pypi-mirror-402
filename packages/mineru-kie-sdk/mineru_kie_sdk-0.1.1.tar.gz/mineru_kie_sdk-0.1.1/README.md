# MinerU KIE SDK

MinerU KIE SDK 是一个用于与 MinerU Knowledge Information Extraction (KIE) 服务交互的 Python SDK。它提供了简单易用的接口来上传文档、查询解析结果等功能。

## 功能特性

- 📄 **文件上传**: 支持 PDF、JPEG、PNG 格式的文件上传
- 🔍 **结果查询**: 自动轮询并获取文档解析、分割、提取结果
- ⚡ **简单易用**: 提供简洁的 Python API，易于集成
- 🔄 **自动重试**: 内置请求重试机制，提高稳定性
- 📊 **类型提示**: 完整的类型提示支持，提升开发体验

## 安装

### 快速安装
```bash
pip install mineru-kie-sdk
```

### 从本地安装

在 mineru_kie_sdk 目录下执行：

```bash
cd kie/mineru_kie_sdk
pip install -e .
```

或者使用 uv：

```bash
cd kie/mineru_kie_sdk
uv pip install -e .
```

### 从源码构建安装包

```bash
cd kie/mineru_kie_sdk
pip install build
python -m build
pip install dist/mineru_kie_sdk-0.1.1-py3-none-any.whl
```

## 快速开始

### 基本使用

```python
from mineru_kie_sdk import MineruKIEClient

# 初始化客户端
client = MineruKIEClient(
    base_url="https://mineru.net/api/kie",
    pipeline_id=YOUR_PIPELINE_ID
)

# 上传文件
file_ids = client.upload_file("document.pdf")
print(f"上传成功，文件ID: {file_ids}")

# 获取解析结果（会自动轮询直到完成）
results = client.get_result(timeout=60)
print(f"解析结果: {results['parse']}")
print(f"分割结果: {results['split']}")
print(f"提取结果: {results['extract']}")
```

### 完整示例

```python
from mineru import MineruKIEClient
from pathlib import Path

# 1. 创建客户端实例
client = MineruKIEClient(
    base_url="https://mineru.net/api/kie",
    pipeline_id=YOUR_PIPELINE_ID,
    timeout=30  # 请求超时时间（秒）
)

# 2. 上传文件
try:
    file_path = Path("example.pdf")
    file_ids = client.upload_file(file_path)
    print(f"✅ 文件上传成功，文件ID: {file_ids}")
except ValueError as e:
    print(f"❌ 文件类型错误: {e}")
except Exception as e:
    print(f"❌ 上传失败: {e}")

# 3. 获取结果
try:
    # timeout=-1 表示一直轮询直到完成
    results = client.get_result(timeout=60, poll_interval=5)
    
    # 访问各个步骤的结果
    parse_result = results["parse"]
    split_result = results["split"]
    extract_result = results["extract"]
    
    if parse_result:
        print("✅ 解析完成")
        print(f"解析结果: {parse_result}")
    
    if split_result:
        print("✅ 分割完成")
        print(f"分割结果: {split_result}")
    
    if extract_result:
        print("✅ 提取完成")
        print(f"提取结果: {extract_result}")
        
except TimeoutError as e:
    print(f"⏱️ 超时: {e}")
except Exception as e:
    print(f"❌ 获取结果失败: {e}")
```

## API 文档

### MineruKIEClient

主要的客户端类，用于与 KIE 服务交互。

#### 初始化参数

- `base_url` (str): API 基础 URL，默认 `"https://mineru.net/api/kie"`
- `pipeline_id` (str): Pipeline ID
- `timeout` (int, 可选): 请求超时时间（秒），默认 30

#### 方法

##### `upload_file(file_path)`

上传文件到服务器。

**参数:**
- `file_path` (str | Path): 要上传的文件路径

**返回:**
- `List[int]`: 上传成功后的文件 ID 列表

**异常:**
- `ValueError`: 文件类型不支持或文件不存在
- `requests.RequestException`: 上传请求失败

**示例:**
```python
file_ids = client.upload_file("document.pdf")
```

##### `get_result(file_ids, timeout=60, poll_interval=5)`

获取文件的解析结果。该方法会轮询服务器直到任务完成或超时。

**参数:**
- `file_ids` (List[int]): 文件 ID 列表。如果查询特定文件，可以手动传入，默认为上传后返回的file_ids
- `timeout` (int): 超时时间（秒）。如果为 -1，则一直轮询直到完成或出错。默认 60
- `poll_interval` (int): 轮询间隔（秒），默认 5

**返回:**
- `Dict[str, Optional[dict]]`: 包含 parse、split、extract 结果的字典

**异常:**
- `ValueError`: 未上传文件或 pipeline_id 无效
- `requests.RequestException`: 请求失败
- `TimeoutError`: 超时

**示例:**
```python
results = client.get_result(timeout=60)
parse_result = results["parse"]
```

### 结果类

#### ParseResult

解析结果类，继承自 `StepResult`。

**方法:**
- `get_result() -> Optional[dict]`: 获取解析结果字典

#### SplitResult

分割结果类，继承自 `StepResult`。

**方法:**
- `get_result() -> Optional[dict]`: 获取分割结果字典

#### ExtractResult

提取结果类，继承自 `StepResult`。

**方法:**
- `get_result() -> Optional[dict]`: 获取提取结果字典

### 工具函数

#### `guess_file_type(file_input)`

检测文件类型。

**参数:**
- `file_input` (str | Path | BytesIO): 文件路径或文件对象

**返回:**
- `Tuple[str, str]`: (文件类型扩展名, MIME类型)，如 `("pdf", "application/pdf")`

**示例:**
```python
from mineru import guess_file_type

file_type, mime_type = guess_file_type("document.pdf")
print(f"文件类型: {file_type}, MIME: {mime_type}")
```

## 支持的文件类型

- PDF (`application/pdf`)
- JPEG (`image/jpeg`)
- PNG (`image/png`)

## 错误处理

SDK 会抛出以下异常：

- `ValueError`: 参数错误或文件类型不支持
- `requests.RequestException`: HTTP 请求失败
- `TimeoutError`: 获取结果超时

建议使用 try-except 块来处理这些异常：

```python
try:
    file_ids = client.upload_file("document.pdf")
    results = client.get_result(timeout=60)
except ValueError as e:
    print(f"参数错误: {e}")
except requests.RequestException as e:
    print(f"请求失败: {e}")
except TimeoutError as e:
    print(f"超时: {e}")
```

## 开发

### 项目结构

```
mineru_kie_sdk/
├── src/
│   └── mineru_kie_sdk/
│       ├── __init__.py      # 包初始化文件，导出主要类和函数
│       ├── common.py        # 通用工具函数
│       └── kie.py           # 主要客户端类
├── pyproject.toml           # 项目配置和依赖
├── README.md                # 本文档
```

### 运行测试

```bash
cd kie/mineru_kie_sdk
pytest
```

### 代码格式化

```bash
cd kie/mineru_kie_sdk
black .
```

## 常见问题

### Q: 为什么一直显示 `requests.RequestException`？

A: 可能有几种情况会导致这个报错：
- pipeline没有部署： 在页面上点击“部署”按钮
- pipeline已存在10个文件，达到上限，需在页面创建新的pipeline
- 传入的文件超出限制：大小超过100M，或页数超过10页
- 传入的文件数量超出限制：当前仅支持单个文件上传


### Q: 上传文件后如何知道处理进度？

A: `get_result()` 方法会自动轮询服务器。你可以通过设置 `poll_interval` 参数来控制轮询频率：

```python
results = client.get_result(timeout=60, poll_interval=5)  # 每5秒轮询一次
```

### Q: 如何处理大文件上传？

A: SDK 使用 `requests` 库进行文件上传，会自动处理大文件。如果遇到超时问题，可以增加 `timeout` 参数：

```python
client = MineruKIEClient(
    base_url="...",
    pipeline_id=YOUR_PIPELINE_ID,
    timeout=300  # 5分钟超时
)
```

### Q: 支持异步操作吗？

A: 当前版本仅支持同步操作。异步支持计划在后续版本中添加。

## 版本历史

### 0.1.1 (2026-01-21)

- 初始版本
- 支持文件上传功能
- 支持结果查询功能
- 支持 PDF、JPEG、PNG 文件格式

## 贡献

欢迎提交 Issue 和 Pull Request！