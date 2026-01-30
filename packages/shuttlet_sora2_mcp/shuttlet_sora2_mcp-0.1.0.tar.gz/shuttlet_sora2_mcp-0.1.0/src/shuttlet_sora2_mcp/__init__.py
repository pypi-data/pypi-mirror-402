"""
Sora2 MCP Server
基于 Sora2 视频模型的 MCP 服务器实现
支持视频生成功能
"""

import os
import requests
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP


# API 配置 - 从环境变量获取
API_BASE_URL = os.environ.get("SORA2_API_BASE_URL", "https://api.lightai.io")
API_KEY = os.environ.get("SORA2_API_KEY", "")

# 创建 MCP server
mcp = FastMCP("Sora2")


@mcp.tool()
def generate_video(
    prompt: str,
    model: str = "sora-2",
    aspect_ratio: str = "16:9",
    hd: bool = False,
    duration: str = "10",
    notify_hook: Optional[str] = None,
    watermark: Optional[bool] = None,
    private: Optional[bool] = None,
) -> dict:
    """
    调用 Sora2 API 生成视频
    
    Args:
        prompt: 视频生成提示词（必需）
        model: 模型名称，必需：
            - sora-2 (默认)
            - sora-2-pro (支持hd、15s)
        aspect_ratio: 输出比例，可选：
            - 16:9 (横屏，默认)
            - 9:16 (竖屏)
        hd: 是否生成高清，默认false；高清会导致生成速度更慢; 仅 sora-2-pro 支持
        duration: 视频时长，可选：
            - 10 (默认)
            - 15
            - 25 (仅 sora-2-pro 支持)
        notify_hook: 通知钩子，可选
        watermark: 是否添加水印，可选
        private: 是否隐藏视频，true-视频不会发布，同时视频无法进行 remix(二次编辑)，默认为 false
    
    Returns:
        API 响应的 JSON 数据，包含生成的视频任务 ID
    """
    url = f"{API_BASE_URL}/v2/videos/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    # 构建请求体
    payload = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "hd": hd,
        "duration": duration
    }
    
    # 添加可选参数
    if notify_hook:
        payload["notify_hook"] = notify_hook
    if watermark is not None:
        payload["watermark"] = watermark
    if private is not None:
        payload["private"] = private
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def generate_video_with_image(
    prompt: str,
    images: List[str],
    model: str = "sora-2",
    aspect_ratio: str = "16:9",
    hd: bool = False,
    duration: str = "10",
    notify_hook: Optional[str] = None,
    watermark: Optional[bool] = None,
    private: Optional[bool] = None,
) -> dict:
    """
    调用 Sora2 API 基于图片生成视频
    
    Args:
        prompt: 视频生成提示词（必需）
        images: 图片列表，支持url、base64（必需）
        model: 模型名称，必需：
            - sora-2 (默认)
            - sora-2-pro (支持hd、15s)
        aspect_ratio: 输出比例，可选：
            - 16:9 (横屏，默认)
            - 9:16 (竖屏)
        hd: 是否生成高清，默认false；高清会导致生成速度更慢; 仅 sora-2-pro 支持
        duration: 视频时长，可选：
            - 10 (默认)
            - 15
            - 25 (仅 sora-2-pro 支持)
        notify_hook: 通知钩子，可选
        watermark: 是否添加水印，可选
        private: 是否隐藏视频，true-视频不会发布，同时视频无法进行 remix(二次编辑)，默认为 false
    
    Returns:
        API 响应的 JSON 数据，包含生成的视频任务 ID
    """
    url = f"{API_BASE_URL}/v2/videos/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    # 构建请求体
    payload = {
        "prompt": prompt,
        "images": images,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "hd": hd,
        "duration": duration
    }
    
    # 添加可选参数
    if notify_hook:
        payload["notify_hook"] = notify_hook
    if watermark is not None:
        payload["watermark"] = watermark
    if private is not None:
        payload["private"] = private
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def generate_storyboard_video(
    prompt: str,
    model: str = "sora-2",
    aspect_ratio: str = "16:9",
    hd: bool = False,
    duration: str = "10",
) -> dict:
    """
    调用 Sora2 API 生成故事板视频
    
    Args:
        prompt: 故事板格式的提示词（必需），格式如下：
            Shot 1:
            duration: 7.5sec
            Scene: 飞机起飞
            
            Shot 2:
            duration: 7.5sec
            Scene: 飞机降落
        model: 模型名称，可选 "sora-2" 或 "sora-2-pro"
        aspect_ratio: 输出比例，可选 "16:9"（横屏）或 "9:16"（竖屏）
        hd: 是否生成高清，默认 false；高清会导致生成速度更慢; 仅 sora-2-pro 支持
        duration: 视频时长，可选 "10"、"15"、"25"（仅 sora-2-pro 支持 25）
    
    Returns:
        API 响应的 JSON 数据，包含生成的视频任务 ID
    """
    url = f"{API_BASE_URL}/v2/videos/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    # 构建请求体
    payload = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "hd": hd,
        "duration": duration
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def generate_video_with_character(
    prompt: str,
    model: str = "sora-2",
    images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    hd: bool = False,
    duration: str = "10",
    character_url: Optional[str] = None,
    character_timestamps: Optional[str] = None,
) -> dict:
    """
    调用 Sora2 API 生成带有角色客串的视频
    
    Args:
        prompt: 视频生成提示词（必需），注意调用角色需要跟 prompt 有空格隔开
            例如：@{角色1Username} 在一个舞台上和 @{角色2Username} 牵手跳舞
        model: 模型名称，可选 "sora-2" 或 "sora-2-pro"
        images: 可选图片列表，支持 url、base64
        aspect_ratio: 输出比例，可选 "16:9"（横屏）或 "9:16"（竖屏）
        hd: 是否生成高清，默认 false；高清会导致生成速度更慢; 仅 sora-2-pro 支持
        duration: 视频时长，可选 "10"、"15"、"25"（仅 sora-2-pro 支持 25）
        character_url: 可选，创建角色需要的视频链接，注意视频中一定不能出现真人
        character_timestamps: 可选，视频角色出现的秒数范围，格式 {start},{end}, 注意 end-start 的范围 1～3秒
    
    Returns:
        API 响应的 JSON 数据，包含生成的视频任务 ID
    """
    url = f"{API_BASE_URL}/v2/videos/generations"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    # 构建请求体
    payload = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "hd": hd,
        "duration": duration
    }
    
    # 添加可选参数
    if images:
        payload["images"] = images
    if character_url:
        payload["character_url"] = character_url
    if character_timestamps:
        payload["character_timestamps"] = character_timestamps
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@mcp.tool()
def list_models() -> dict:
    """
    列出所有可用的 Sora2 模型及其特性
    
    Returns:
        包含所有模型信息的字典
    """
    return {
        "models": [
            {
                "name": "sora-2",
                "description": "标准版",
                "features": ["视频生成", "故事板", "角色客串"]
            },
            {
                "name": "sora-2-pro",
                "description": "专业版，支持高清和更长时长",
                "features": ["视频生成", "故事板", "角色客串", "高清画质", "25秒时长"]
            }
        ],
        "format_options": ["16:9横屏", "9:16竖屏", "高清", "10秒", "15秒", "25秒(仅pro支持)"],
        "features": ["故事板视频", "角色客串", "多模态输入"]
    }


@mcp.tool()
def get_video_task(task_id: str) -> dict:
    """
    查询 Sora2 视频生成任务状态
    
    Args:
        task_id: 任务 ID（必需）
    
    Returns:
        任务状态信息，包含以下字段：
            - task_id: 任务 ID
            - platform: 平台
            - action: 操作类型
            - status: 状态（NOT_START/IN_PROGRESS/SUCCESS/FAILURE）
            - fail_reason: 失败原因
            - submit_time: 提交时间
            - start_time: 开始时间
            - finish_time: 完成时间
            - progress: 进度
            - data: 数据
            - search_item: 搜索项
    """
    url = f"{API_BASE_URL}/v2/videos/generations/{task_id}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def main() -> None:
    """
    主函数，启动 MCP 服务器
    """
    mcp.run(transport="stdio")
