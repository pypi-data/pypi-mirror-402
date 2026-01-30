"""
Nano-banana MCP Server
基于 gemini-2.5-flash-image-preview 优化的画图 API
支持图像生成和图像编辑功能
"""

import os
import requests
from pathlib import Path
from typing import Optional
from io import BytesIO
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP


# API 配置 - 从环境变量获取
API_BASE_URL = os.environ.get("NANO_BANANA_API_BASE_URL", "https://api.lightai.io")
API_KEY = os.environ.get("NANO_BANANA_API_KEY", "")

# 创建 MCP server
mcp = FastMCP("Nano-Banana")

def _get_mime_type(file_path: Path) -> str:
    """根据文件扩展名获取 MIME 类型"""
    suffix = file_path.suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mime_types.get(suffix, "application/octet-stream")


@mcp.tool()
def generate_image(
    prompt: str,
    model: str = "nano-banana",
    response_format: str = "url",
    aspect_ratio: Optional[str] = None,
    image: Optional[str] = None,
    image_size: Optional[str] = None,
) -> dict:
    """
    调用 Nano-banana API 生成图像
    
    Args:
        prompt: 图像生成提示词（必需）
        model: 模型名称，可选 "nano-banana"(标准版)、"nano-banana-hd"(高清版4K画质)、"nano-banana-2"(支持image_size参数)
        response_format: 返回格式，"url" 或 "b64_json"
        aspect_ratio: 图片比例，如 "4:3", "16:9", "1:1", "2:3", "3:2", "3:4", "4:5", "5:4", "9:16", "21:9"
        image: 参考图 URL（多个用逗号分隔）
        image_size: 图片尺寸（仅 nano-banana-2 支持），可选 "1K", "2K", "4K"
    
    Returns:
        API 响应的 JSON 数据，包含生成的图像 URL 或 base64 数据
    """
    url = f"{API_BASE_URL}/v1/images/generations"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建请求体
    payload = {
        "model": model,
        "prompt": prompt,
    }
    
    # 添加可选参数
    if response_format:
        payload["response_format"] = response_format
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if image:
        # 支持逗号分隔的多个 URL
        image_list = [img.strip() for img in image.split(",")]
        payload["image"] = image_list
    if image_size:
        payload["image_size"] = image_size
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


@mcp.tool()
def edit_image(
    prompt: str,
    image: str,
    model: str = "nano-banana",
    response_format: str = "url",
    aspect_ratio: Optional[str] = None,
    image_size: Optional[str] = None,
) -> dict:
    """
    调用 Nano-banana Edit API 编辑图像
    
    Args:
        prompt: 图像编辑提示词（必需）
        image: 参考图片路径或 URL（必需，多个用逗号分隔）
        model: 模型名称，可选 "nano-banana"(标准版)、"nano-banana-hd"(高清版4K画质)、"nano-banana-2"(支持image_size参数)
        response_format: 返回格式，"url" 或 "b64_json"
        aspect_ratio: 图片比例，如 "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
        image_size: 图片尺寸（仅 nano-banana-2 支持），可选 "1K", "2K", "4K"
    
    Returns:
        API 响应的 JSON 数据，包含编辑后的图像 URL 或 base64 数据
    """
    url = f"{API_BASE_URL}/v1/images/edits"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    
    # 构建 multipart/form-data 数据
    data = {
        "model": model,
        "prompt": prompt,
    }
    
    # 添加可选参数
    if response_format:
        data["response_format"] = response_format
    if aspect_ratio:
        data["aspect_ratio"] = aspect_ratio
    if image_size:
        data["image_size"] = image_size
    
    # 处理图片参数
    files = []
    
    # 确保 image 是列表
    if not isinstance(image, list):
        image = [image]
    
    for img in image:
        # 判断是文件路径还是 URL
        if isinstance(img, str) and (img.startswith("http://") or img.startswith("https://")):
            # 如果是 URL，下载图片并添加到 files 列表
            img_response = requests.get(img)
            img_response.raise_for_status()
            
            # 从 URL 中提取文件名
            parsed_url = urlparse(img)
            filename = Path(parsed_url.path).name or "image.png"
            
            # 从响应头获取 MIME 类型，或根据 URL 推断
            content_type = img_response.headers.get("Content-Type", "").split(";")[0].strip()
            if not content_type or content_type == "application/octet-stream":
                content_type = _get_mime_type(Path(filename))
            print(content_type)
            files.append(
                ("image", (filename, BytesIO(img_response.content), content_type))
            )
        else:
            img_path = Path(img) if isinstance(img, str) else img
            if img_path.exists():
                # 如果是本地文件，添加到 files 列表
                files.append(
                    ("image", (img_path.name, open(img_path, "rb"), _get_mime_type(img_path)))
                )
            else:
                raise FileNotFoundError(f"图片文件不存在: {img}")
    
    try:
        # 发送请求，统一使用 multipart/form-data 格式
        response = requests.post(url, headers=headers, data=data, files=files if files else None)
        
        response.raise_for_status()
        return response.json()
    finally:
        # 关闭文件句柄
        for _, file_tuple in files:
            file_tuple[1].close()


@mcp.tool()
def list_models() -> dict:
    """
    列出所有可用的 Nano-banana 模型及其特性
    
    Returns:
        包含所有模型信息的字典
    """
    return {
        "models": [
            {
                "name": "nano-banana",
                "description": "标准版，适合一般图像生成和编辑",
                "features": ["图像生成", "图像编辑", "参考图支持", "比例设置"]
            },
            {
                "name": "nano-banana-hd",
                "description": "高清版，4K 画质输出",
                "features": ["图像生成", "图像编辑", "参考图支持", "比例设置", "4K画质"]
            },
            {
                "name": "nano-banana-2",
                "description": "增强版，支持自定义图片尺寸",
                "features": ["图像生成", "图像编辑", "参考图支持", "比例设置", "自定义尺寸(1K/2K/4K)"]
            }
        ],
        "aspect_ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "image_sizes": ["1K", "2K", "4K"],
        "response_formats": ["url", "b64_json"]
    }

def main() -> None:
    mcp.run(transport="stdio")
