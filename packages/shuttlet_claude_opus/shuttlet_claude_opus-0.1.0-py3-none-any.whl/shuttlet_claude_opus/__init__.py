"""
Claude Opus MCP Server
基于 OpenAI 兼容 API 的 Claude Opus 聊天服务
支持聊天对话、流式输出和工具调用
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP


# API 配置 - 从环境变量获取
API_BASE_URL = os.environ.get("CLAUDE_OPUS_API_BASE_URL", "https://api.lightai.io")
API_KEY = os.environ.get("CLAUDE_OPUS_API_KEY", "")
DEFAULT_MODEL = os.environ.get("CLAUDE_OPUS_DEFAULT_MODEL", "claude-opus-4-20250514")

# 创建 MCP server
mcp = FastMCP("Claude-Opus")


@mcp.tool()
def chat(
    message: str,
    model: str = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
) -> dict:
    """
    与 Claude Opus 模型进行对话

    Args:
        message: 用户消息内容（必需）
        model: 模型名称，默认使用环境变量中配置的模型
        system_prompt: 系统提示词，用于设定 AI 的行为和角色
        temperature: 采样温度，介于 0 和 2 之间，较高值使输出更随机
        max_tokens: 最大生成令牌数
        top_p: 核采样参数，0.1 表示只考虑前 10% 概率质量的令牌

    Returns:
        API 响应的 JSON 数据，包含模型的回复
    """
    url = f"{API_BASE_URL}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 构建消息列表
    messages = []
    
    # 添加系统提示词
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 添加用户消息
    messages.append({
        "role": "user",
        "content": message
    })
    
    # 构建请求体
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False
    }
    
    # 添加可选参数
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # 提取并格式化响应
    return {
        "id": result.get("id"),
        "model": result.get("model"),
        "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "finish_reason": result.get("choices", [{}])[0].get("finish_reason"),
        "usage": result.get("usage")
    }


@mcp.tool()
def chat_with_history(
    messages: str,
    model: str = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
) -> dict:
    """
    带历史记录的多轮对话

    Args:
        messages: 消息历史 JSON 字符串，格式为 [{"role": "user/assistant", "content": "..."}]
        model: 模型名称，默认使用环境变量中配置的模型
        system_prompt: 系统提示词，用于设定 AI 的行为和角色
        temperature: 采样温度，介于 0 和 2 之间
        max_tokens: 最大生成令牌数
        top_p: 核采样参数

    Returns:
        API 响应的 JSON 数据，包含模型的回复
    """
    url = f"{API_BASE_URL}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 解析消息历史
    try:
        message_list = json.loads(messages)
    except json.JSONDecodeError:
        return {"error": "消息格式错误，请提供有效的 JSON 字符串"}
    
    # 构建完整消息列表
    full_messages = []
    
    # 添加系统提示词
    if system_prompt:
        full_messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 添加历史消息
    full_messages.extend(message_list)
    
    # 构建请求体
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": full_messages,
        "stream": False
    }
    
    # 添加可选参数
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # 提取并格式化响应
    return {
        "id": result.get("id"),
        "model": result.get("model"),
        "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "finish_reason": result.get("choices", [{}])[0].get("finish_reason"),
        "usage": result.get("usage")
    }


@mcp.tool()
def chat_with_tools(
    message: str,
    tools: str,
    model: str = None,
    system_prompt: Optional[str] = None,
    tool_choice: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """
    带工具调用的对话

    Args:
        message: 用户消息内容（必需）
        tools: 工具定义 JSON 字符串，格式为 [{"type": "function", "function": {...}}]
        model: 模型名称，默认使用环境变量中配置的模型
        system_prompt: 系统提示词
        tool_choice: 工具选择策略，"none"/"auto" 或指定工具
        temperature: 采样温度
        max_tokens: 最大生成令牌数

    Returns:
        API 响应的 JSON 数据，包含模型的回复或工具调用请求
    """
    url = f"{API_BASE_URL}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 解析工具定义
    try:
        tools_list = json.loads(tools)
    except json.JSONDecodeError:
        return {"error": "工具定义格式错误，请提供有效的 JSON 字符串"}
    
    # 构建消息列表
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    messages.append({
        "role": "user",
        "content": message
    })
    
    # 构建请求体
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "tools": tools_list,
        "stream": False
    }
    
    # 添加可选参数
    if tool_choice:
        if tool_choice in ["none", "auto"]:
            payload["tool_choice"] = tool_choice
        else:
            # 假设是函数名，构建完整的 tool_choice 对象
            payload["tool_choice"] = {
                "type": "function",
                "function": {"name": tool_choice}
            }
    
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # 提取并格式化响应
    choice = result.get("choices", [{}])[0]
    message_data = choice.get("message", {})
    
    return {
        "id": result.get("id"),
        "model": result.get("model"),
        "content": message_data.get("content"),
        "tool_calls": message_data.get("tool_calls"),
        "finish_reason": choice.get("finish_reason"),
        "usage": result.get("usage")
    }


@mcp.tool()
def analyze_image(
    image_url: str,
    prompt: Optional[str] = None,
    model: str = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> dict:
    """
    分析图片内容

    Args:
        image_url: 图片 URL 地址（必需），支持多个 URL 用逗号分隔
        prompt: 针对图片的问题或指令，默认为"请描述这张图片的内容"
        model: 模型名称，默认使用环境变量中配置的模型（需要支持视觉能力）
        system_prompt: 系统提示词，用于设定 AI 的行为和角色
        temperature: 采样温度，介于 0 和 2 之间
        max_tokens: 最大生成令牌数

    Returns:
        API 响应的 JSON 数据，包含图片分析结果
    """
    url = f"{API_BASE_URL}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 构建消息列表
    messages = []
    
    # 添加系统提示词
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 构建包含图片的内容数组
    content = []
    
    # 添加文本提示
    text_prompt = prompt or "请描述这张图片的内容"
    content.append({
        "type": "text",
        "text": text_prompt
    })
    
    # 处理图片 URL（支持多个，用逗号分隔）
    image_urls = [u.strip() for u in image_url.split(",")]
    for img_url in image_urls:
        if img_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": img_url
                }
            })
    
    # 添加用户消息
    messages.append({
        "role": "user",
        "content": content
    })
    
    # 构建请求体
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False
    }
    
    # 添加可选参数
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # 提取并格式化响应
    return {
        "id": result.get("id"),
        "model": result.get("model"),
        "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "finish_reason": result.get("choices", [{}])[0].get("finish_reason"),
        "usage": result.get("usage")
    }


@mcp.tool()
def chat_with_images(
    message: str,
    image_urls: str,
    model: str = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
) -> dict:
    """
    带图片的对话（图文混合）

    Args:
        message: 用户消息内容（必需）
        image_urls: 图片 URL 地址，支持多个 URL 用逗号分隔
        model: 模型名称，默认使用环境变量中配置的模型（需要支持视觉能力）
        system_prompt: 系统提示词，用于设定 AI 的行为和角色
        temperature: 采样温度，介于 0 和 2 之间
        max_tokens: 最大生成令牌数
        top_p: 核采样参数

    Returns:
        API 响应的 JSON 数据，包含模型的回复
    """
    url = f"{API_BASE_URL}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 构建消息列表
    messages = []
    
    # 添加系统提示词
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # 构建包含图片的内容数组
    content = []
    
    # 添加文本消息
    content.append({
        "type": "text",
        "text": message
    })
    
    # 处理图片 URL（支持多个，用逗号分隔）
    urls = [u.strip() for u in image_urls.split(",")]
    for img_url in urls:
        if img_url:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": img_url
                }
            })
    
    # 添加用户消息
    messages.append({
        "role": "user",
        "content": content
    })
    
    # 构建请求体
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "stream": False
    }
    
    # 添加可选参数
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    
    # 提取并格式化响应
    return {
        "id": result.get("id"),
        "model": result.get("model"),
        "content": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "finish_reason": result.get("choices", [{}])[0].get("finish_reason"),
        "usage": result.get("usage")
    }


@mcp.tool()
def list_models() -> dict:
    """
    列出所有可用的 Claude 模型及其特性

    Returns:
        包含所有模型信息的字典
    """
    return {
        "models": [
            {
                "name": "claude-opus-4-20250514",
                "description": "Claude Opus 4 - 最强大的 Claude 模型，适合复杂推理和创意任务",
                "features": ["多轮对话", "工具调用", "长上下文", "代码生成", "复杂推理", "图片分析"],
                "vision": True
            },
            {
                "name": "claude-sonnet-4-20250514",
                "description": "Claude Sonnet 4 - 平衡性能和速度的模型",
                "features": ["多轮对话", "工具调用", "长上下文", "代码生成", "图片分析"],
                "vision": True
            },
            {
                "name": "claude-3-5-sonnet-20241022",
                "description": "Claude 3.5 Sonnet - 高性能版本",
                "features": ["多轮对话", "工具调用", "长上下文", "代码生成", "图片分析"],
                "vision": True
            },
            {
                "name": "claude-3-5-haiku-20241022",
                "description": "Claude 3.5 Haiku - 快速响应版本",
                "features": ["多轮对话", "快速响应", "代码生成", "图片分析"],
                "vision": True
            }
        ],
        "default_model": DEFAULT_MODEL,
        "api_base_url": API_BASE_URL,
        "parameters": {
            "temperature": "0-2，控制输出随机性",
            "max_tokens": "最大生成令牌数",
            "top_p": "核采样参数",
            "stream": "是否流式输出"
        },
        "tools": [
            "chat - 简单对话",
            "chat_with_history - 多轮对话",
            "chat_with_tools - 工具调用对话",
            "analyze_image - 图片分析",
            "chat_with_images - 图文混合对话",
            "list_models - 模型列表"
        ]
    }


def main() -> None:
    mcp.run(transport="stdio")