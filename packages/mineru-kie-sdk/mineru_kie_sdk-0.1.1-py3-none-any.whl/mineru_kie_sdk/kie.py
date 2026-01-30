"""
MinerU KIE SDK 客户端模块
提供文件上传和结果查询功能
"""
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .common import guess_file_type


class StepResult(object):
    """步骤结果基类"""
    def __init__(self, step_result: Optional[dict]):
        self.step_result = step_result

    def get_result(self) -> Optional[dict]:
        """
        获取步骤结果
        
        Returns:
            Optional[dict]: 步骤结果字典，如果未完成则返回 None
        """
        return self.step_result


class ParseResult(StepResult):
    """
    解析结果类
    用于存储和访问文档解析步骤的结果
    """
    def __init__(self, parse_result: Optional[dict]):
        super().__init__(parse_result)


class SplitResult(StepResult):
    """
    分割结果类
    用于存储和访问文档分割步骤的结果
    """
    def __init__(self, split_result: Optional[dict]):
        super().__init__(split_result)


class ExtractResult(StepResult):
    """
    提取结果类
    用于存储和访问文档提取步骤的结果
    """
    def __init__(self, extract_result: Optional[dict]):
        super().__init__(extract_result)


class MineruKIEClient:
    """
    用于与 MinerU KIE 服务进行交互，支持文件上传和结果查询功能。
    
    Attributes:
        base_url (str): API 基础 URL
        pipeline_id (str): Pipeline ID（字符串，通常是 UUID）
        file_ids (List[int]): 上传的文件 ID 列表
        parse (ParseResult): 解析结果
        split (SplitResult): 分割结果
        extract (ExtractResult): 提取结果
    """
    
    def __init__(
        self,
        pipeline_id: str,
        base_url: str = "https://mineru.net/api/kie",
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip('/')
        self.pipeline_id = pipeline_id
        self.file_ids: List[int] = []
        self.parse = ParseResult(None)
        self.split = SplitResult(None)
        self.extract = ExtractResult(None)
        
        # 创建带重试机制的会话
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.timeout = timeout
        
        # 设置默认请求头（上传时会自动设置 Content-Type）
        self.headers = {}

    def upload_file(
        self,
        file_path: Union[str, Path]
    ) -> List[int]:
        """
        上传文件到服务器
        
        根据 UploadFileView.post() 方法实现：
        - 路径: POST /api/kie/restful/pipelines/{pipeline_id}/upload
        - 字段名: "files"
        - 响应: {"code": "succ", "msg": "", "data": {"pipeline_id": "...", "files": [{"file_id": ...}]}}
        
        Args:
            file_path: 要上传的文件路径
        
        Returns:
            List[int]: 上传成功后的文件 ID 列表
        """
        file_path = Path(file_path)
        
        # 检查文件是否存在
        if not file_path.exists():
            raise ValueError(f"文件不存在: {file_path}")
        
        # 检查文件类型
        file_type, file_mime = guess_file_type(file_path)
        if file_type is None:
            raise ValueError(f"无法识别文件类型，或不支持的文件类型: {file_mime}")
        
        # 构建上传 URL（与 UploadFileView 的路径一致）
        upload_url = f"{self.base_url}/restful/pipelines/{self.pipeline_id}/upload"
        
        try:
            with open(file_path, 'rb') as f:
                files = {"files": (file_path.name, f, file_mime)}
                
                # 上传文件时不需要手动设置 Content-Type，requests 会自动设置
                response = self.session.post(
                    upload_url,
                    files=files,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # 解析响应（与 api_success 返回格式一致）
                result = response.json()
                if result.get("code") != "succ":
                    raise requests.RequestException(
                        f"上传失败: {result.get('msg', '未知错误')}"
                    )
                
                # 提取文件 ID（与 FileUploadResponseSerializer 格式一致）
                data = result.get("data", {})
                files_info = data.get("files", [])
                file_ids = [file_info["file_id"] for file_info in files_info]
                
                # 保存文件 ID
                self.file_ids.extend(file_ids)
                
                return file_ids
                
        except requests.RequestException as e:
            raise requests.RequestException(f"上传文件失败: {str(e)}")

    def get_result(
        self,
        file_ids: List[int] = [],
        timeout: int = 60,
        poll_interval: int = 10
    ) -> Dict[str, Optional[dict]]:
        """
        获取文件的解析结果
        
        根据 GetFileResultView.get() 方法实现：
        - 路径: GET /api/kie/restful/pipelines/{pipeline_id}/result
        - 响应包含: pipeline_id, pipeline_name, pipeline_status, pipeline_steps, file_status
        - file_status 中每个文件包含: code, msg, file_id, doc_name, doc_type, cur_step, 
          step_status, parse_result, split_result, extract_result
        
        该方法会轮询服务器直到任务完成或超时。
        
        Args:
            timeout: 超时时间（秒）。如果为 -1，则一直轮询直到完成或出错。默认 60
            poll_interval: 轮询间隔（秒），默认 2
        
        Returns:
            Dict[str, Optional[dict]]: 包含 parse、split、extract 结果的字典
        
        Raises:
            ValueError: 未上传文件或 pipeline_id 无效
            requests.RequestException: 请求失败
            TimeoutError: 超时
        """
        if not file_ids:
            file_ids = self.file_ids
        if not file_ids:
            raise ValueError("请先上传文件，或输入正确的文件id")
        if len(file_ids) > 1:
            raise ValueError("仅支持单个文件查询")
        
        # 构建结果查询 URL（与 GetFileResultView 的路径一致）
        result_url = f"{self.base_url}/restful/pipelines/{self.pipeline_id}/result"
        
        start_time = time.time()
        
        while True:
            # 检查超时
            if timeout > 0 and time.time() - start_time > timeout:
                raise TimeoutError(f"获取结果超时（{timeout}秒）")
            
            try:
                response = self.session.get(
                    result_url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") != "succ":
                    raise requests.RequestException(
                        f"获取结果失败: {result.get('msg', '未知错误')}"
                    )
                
                # 解析响应（与 StepExecuteStatusResponseSerializer 格式一致）
                data = result.get("data", {})
                file_status_list = data.get("file_status", [])
                
                for file_status in file_status_list:
                    file_id = file_status.get("file_id")
                    if file_id not in file_ids:
                        continue
                    
                    code = int(file_status.get("code", 1))
                    msg = file_status.get("msg", "")
                    
                    # 更新结果（与 API 返回的字段名一致）
                    self.parse = ParseResult(file_status.get("parse_result"))
                    self.split = SplitResult(file_status.get("split_result"))
                    self.extract = ExtractResult(file_status.get("extract_result"))
                    
                    # 检查状态（与 check_file_process_status 的返回值一致）
                    # code: 0=成功完成, 1=进行中, -1=失败, -2=等待执行
                    if code == 0:  # 成功完成
                        return {
                        "parse": self.parse.get_result(),
                        "split": self.split.get_result(),
                        "extract": self.extract.get_result()
                    }
                    elif code == -1:  # 失败
                        raise requests.RequestException(f"处理失败: {msg}")
                    elif code == -2:  # 等待执行
                        time.sleep(poll_interval)
                        continue
                    elif code == 1:  # 进行中 (code == 1)
                        time.sleep(poll_interval)
                        continue
                    else:
                        raise ValueError("未知的返回代码")
                
                # 等待后继续轮询
                time.sleep(poll_interval)
                
            except requests.RequestException as e:
                if "处理失败" in str(e):
                    raise
                # 其他请求错误，等待后重试
                time.sleep(poll_interval)
                continue
