#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云图像超分辨率 MCP 服务器
提供图像超分辨率增强功能
"""

import io
import logging
import os
import time
from typing import Literal, Optional
from urllib.request import urlopen

from alibabacloud_imageenhan20190930.client import Client as ImageEnhanClient
from alibabacloud_imageenhan20190930.models import GenerateSuperResolutionImageAdvanceRequest
from alibabacloud_viapi20230117.client import Client as ViapiClient
from alibabacloud_viapi20230117.models import GetAsyncJobResultRequest
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from mcp.server.fastmcp import FastMCP

# 配置日志
logging.basicConfig(
    level=logging.INFO if os.getenv("MCP_DEBUG") == "1" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("阿里云图像超分辨率")


def get_imageenhan_client() -> ImageEnhanClient:
    """获取图像增强客户端实例"""
    config = Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        endpoint="imageenhan.cn-shanghai.aliyuncs.com",
        region_id="cn-shanghai",
    )
    return ImageEnhanClient(config)


def get_viapi_client() -> ViapiClient:
    """获取 VIAPI 客户端实例（用于查询任务状态）"""
    config = Config(
        access_key_id=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"),
        access_key_secret=os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"),
        endpoint="viapi.cn-shanghai.aliyuncs.com",
        region_id="cn-shanghai",
    )
    return ViapiClient(config)


def verify_credentials():
    """验证环境变量是否配置"""
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID"):
        raise ValueError("未设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID")
    if not os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET"):
        raise ValueError("未设置环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET")


def _poll_task_with_timeout(
    job_id: str,
    timeout_seconds: int = 170,
    interval_seconds: int = 5
) -> Optional[dict]:
    """
    轮询任务状态直到完成或超时
    
    Args:
        job_id: 任务ID
        timeout_seconds: 超时时间（秒），默认170秒
        interval_seconds: 轮询间隔（秒），默认5秒
    
    Returns:
        如果任务完成返回结果字典，超时返回 None
    """
    start_time = time.time()
    timeout_ms = timeout_seconds * 1000
    interval_ms = interval_seconds
    
    logger.info(f"开始轮询任务 {job_id}，超时时间 {timeout_seconds} 秒")
    
    while (time.time() - start_time) * 1000 < timeout_ms:
        try:
            # 调用查询任务函数
            result = query_task_status(job_id)
            
            status = result.get("status", "")
            
            # 检查任务是否完成或失败
            if status in ["SUCCESS", "PROCESS_SUCCESS"]:
                logger.info(f"任务 {job_id} 已完成")
                return result
            elif status in ["FAILED", "PROCESS_FAILED"]:
                logger.error(f"任务 {job_id} 失败")
                return result
            
            # 任务仍在进行中
            logger.info(f"任务 {job_id} 状态: {status}")
            
        except Exception as e:
            logger.error(f"轮询任务 {job_id} 时发生异常: {e}")
        
        # 等待下一次轮询
        time.sleep(interval_ms)
    
    logger.warning(f"任务 {job_id} 轮询超时")
    return None


@mcp.tool()
def submit_super_resolution_task(
    image_url: str,
    scale: Literal[2, 3, 4] = 2,
    output_format: Literal["jpg", "png"] = "jpg",
    output_quality: int = 100,
) -> dict:
    """
    提交图像超分辨率处理任务（自动轮询170秒）

    支持任意可访问的图片 URL，无需限制为阿里云 OSS。
    任务提交后会自动轮询170秒，如果在此期间完成则直接返回结果，
    否则返回任务ID供后续手动查询。

    Args:
        image_url: 图像的URL地址（支持任意可访问的 HTTP/HTTPS URL）
        scale: 放大倍数，可选值：2、3、4
        output_format: 输出格式，可选 jpg 或 png
        output_quality: 输出质量（1-100）

    Returns:
        如果170秒内完成：返回包含 output_url 的完整结果
        如果超时未完成：返回任务ID，提示用户稍后手动查询

    Raises:
        ValueError: 参数验证失败
        RuntimeError: API 调用失败
    """
    verify_credentials()

    # 验证参数
    if output_quality < 1 or output_quality > 100:
        raise ValueError("output_quality 必须在 1-100 之间")

    client = get_imageenhan_client()

    # 使用 Advance 方法支持任意 URL
    # 下载图片内容到内存
    logger.info(f"下载图片: {image_url}")
    try:
        img_data = urlopen(image_url).read()
        img_stream = io.BytesIO(img_data)
        logger.info(f"图片下载成功，大小: {len(img_data)} 字节")
    except Exception as e:
        raise RuntimeError(f"无法下载图片: {e}")

    # 创建 AdvanceRequest
    request = GenerateSuperResolutionImageAdvanceRequest(
        image_url_object=img_stream,
        scale=scale,
        output_format=output_format,
        output_quality=output_quality,
    )

    runtime = RuntimeOptions()

    # 调用 Advance API
    response = client.generate_super_resolution_image_advance(request, runtime)

    # 检查响应数据
    if not response.body:
        raise RuntimeError("API 返回的响应体为空")

    # 记录完整响应用于调试
    logger.info(f"API 响应: {response.body}")

    # 获取 job_id
    job_id = None
    
    # 异步模式处理（data 为 None 但有 message）
    if not response.body.data:
        message = getattr(response.body, 'message', '')
        if '异步调用' in message or '任务已提交' in message:
            job_id = response.body.request_id  # request_id 就是 job_id
        else:
            # API 错误
            error_details = {
                "request_id": response.body.request_id,
                "code": getattr(response.body, 'code', None),
                "message": message,
            }
            raise RuntimeError(f"API 未返回处理结果。RequestId: {response.body.request_id}, 详细信息: {error_details}")
    
    # 如果 data 中包含 job_id，使用它
    elif hasattr(response.body.data, 'job_id'):
        job_id = response.body.data.job_id
    
    # 其他未知情况
    else:
        raise RuntimeError(f"API 返回格式异常，响应内容: {response.body}")
    
    # 开始轮询任务状态（170秒超时）
    logger.info(f"图像超分任务已提交，任务ID: {job_id}，开始轮询...")
    polled_result = _poll_task_with_timeout(job_id, timeout_seconds=170, interval_seconds=5)
    
    if polled_result:
        # 轮询成功，返回完整结果
        return polled_result
    else:
        # 轮询超时，返回任务ID
        return {
            "success": True,
            "request_id": response.body.request_id,
            "job_id": job_id,
            "scale": scale,
            "status": "SUBMITTED",
            "message": "✅ 图像超分任务已提交",
            "user_notice": "任务正在后台处理中（约10-30秒）。完成后会在右上角弹出通知，届时可直接点击通知查看结果。您现在可以继续其他操作，无需等待。",
        }


@mcp.tool()
def query_task_status(job_id: str) -> dict:
    """
    查询异步任务的处理状态和结果（可选）
    
    注意：任务处理完成后会自动推送通知，通常无需主动调用此工具。
    此工具仅在需要手动检查任务状态时使用。
    
    Args:
        job_id: 任务ID
    
    Returns:
        包含任务状态和结果的字典
        - status: PROCESSING(处理中) / SUCCESS(成功) / FAILED(失败)
        - output_url: 处理成功后的图片URL（仅在成功时返回）
    """
    verify_credentials()

    client = get_viapi_client()

    # 创建查询请求
    request = GetAsyncJobResultRequest(job_id=job_id)

    runtime = RuntimeOptions()

    # 调用查询API（如果失败会抛出异常）
    response = client.get_async_job_result_with_options(request, runtime)

    # 解析状态
    status = response.body.data.status
    result = {
        "success": True,
        "job_id": job_id,
        "status": status,
        "request_id": response.body.request_id,
    }

    # 如果任务完成，添加结果URL
    if status in ["SUCCESS", "PROCESS_SUCCESS"]:
        # 支持两种成功状态：SUCCESS 和 PROCESS_SUCCESS
        result_url = getattr(response.body.data, "result", None) or \
                     getattr(response.body.data, "Result", None)
        if result_url:
            result["output_url"] = result_url
            result["message"] = "任务处理成功"
        else:
            result["message"] = "任务已完成，但未返回结果 URL"
    elif status == "PROCESSING":
        result["message"] = "任务处理中，完成后将自动推送通知"
    elif status in ["FAILED", "PROCESS_FAILED"]:
        # 处理失败状态（FAILED 或 PROCESS_FAILED）
        # 注意：属性名是首字母大写的 ErrorCode 和 ErrorMessage
        error_msg = getattr(response.body.data, "error_message", None) or \
                    getattr(response.body.data, "ErrorMessage", "未知错误")
        error_code = getattr(response.body.data, "error_code", None) or \
                     getattr(response.body.data, "ErrorCode", "UNKNOWN")
        result["message"] = "任务处理失败"
        result["error_message"] = error_msg
        result["error_code"] = error_code
        # 任务失败时抛出异常，让 isError = true
        raise RuntimeError(f"任务处理失败 [{error_code}]: {error_msg}")
    else:
        # 未知状态
        result["message"] = f"未知状态: {status}"

    return result


def main():
    """主函数入口"""
    logger.info("启动阿里云图像超分辨率 MCP 服务器...")
    mcp.run()


if __name__ == "__main__":
    main()
