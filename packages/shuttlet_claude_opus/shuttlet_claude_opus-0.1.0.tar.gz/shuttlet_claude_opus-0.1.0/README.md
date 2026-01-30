# Claude Opus MCP Server

基于 OpenAI 兼容 API 的 Claude Opus 聊天服务 MCP Server，支持对话、多轮对话、工具调用和图片分析功能。

## 功能特性

- **简单对话** (`chat`): 与 Claude 进行单轮对话
- **多轮对话** (`chat_with_history`): 支持上下文的多轮对话
- **工具调用** (`chat_with_tools`): 支持函数调用的对话
- **图片分析** (`analyze_image`): 分析图片内容，支持多图
- **图文混合对话** (`chat_with_images`): 带图片的对话
- **模型列表** (`list_models`): 列出所有可用模型及其特性

## 可用模型

| 模型名称 | 描述 | 视觉能力 |
|---------|------|---------|
| `claude-opus-4-20250514` | Claude Opus 4 - 最强大的模型，适合复杂推理 | ✅ |
| `claude-sonnet-4-20250514` | Claude Sonnet 4 - 平衡性能和速度 | ✅ |
| `claude-3-5-sonnet-20241022` | Claude 3.5 Sonnet - 高性能版本 | ✅ |
| `claude-3-5-haiku-20241022` | Claude 3.5 Haiku - 快速响应版本 | ✅ |

## 环境变量

| 变量名 | 必需 | 默认值 | 描述 |
|-------|------|--------|------|
| `CLAUDE_OPUS_API_KEY` | ✅ | - | API 密钥 |
| `CLAUDE_OPUS_API_BASE_URL` | ❌ | `https://api.lightai.io` | API 基础 URL |
| `CLAUDE_OPUS_DEFAULT_MODEL` | ❌ | `claude-opus-4-20250514` | 默认使用的模型 |

## Cursor MCP 配置

### uvx 运行（推荐）

在 Cursor 的 `~/.cursor/mcp.json` 中添加以下配置：

```json
{
  "mcpServers": {
    "claude-opus": {
      "command": "uvx",
      "args": [
        "shuttlet_claude_opus"
      ],
      "env": {
        "CLAUDE_OPUS_API_KEY": "your-api-key-here",
        "CLAUDE_OPUS_API_BASE_URL": "https://api.lightai.io",
        "CLAUDE_OPUS_DEFAULT_MODEL": "claude-opus-4-20250514"
      }
    }
  }
}
```

### 本地运行

```json
{
  "mcpServers": {
    "claude-opus": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/shuttlet_claude_opus",
        "run",
        "python",
        "-m",
        "shuttlet_claude_opus"
      ],
      "env": {
        "CLAUDE_OPUS_API_KEY": "your-api-key-here",
        "CLAUDE_OPUS_API_BASE_URL": "https://api.lightai.io"
      }
    }
  }
}
```

> ⚠️ 请将 `your-api-key-here` 替换为你的实际 API 密钥。

## 使用示例

配置完成后，在 Cursor 中可以使用以下工具：

### 简单对话

```
请帮我解释一下什么是机器学习
```

### 带系统提示的对话

```
使用 Claude Opus 作为一个 Python 专家来帮我优化代码
```

### 多轮对话

```
继续之前的对话，深入探讨这个话题
```

### 工具调用

```
使用 Claude 分析数据并调用计算函数
```

### 图片分析

```
分析这张图片: https://example.com/image.jpg
```

### 图文混合对话

```
这两张图片有什么区别？
图片1: https://example.com/image1.jpg
图片2: https://example.com/image2.jpg
```

### 查看可用模型

```
列出所有可用的 Claude 模型
```

## API 参数说明

### 通用参数

| 参数 | 类型 | 描述 |
|-----|------|------|
| `message` | string | 用户消息内容（必需） |
| `model` | string | 模型名称 |
| `system_prompt` | string | 系统提示词 |
| `temperature` | float | 采样温度 (0-2)，较高值输出更随机 |
| `max_tokens` | int | 最大生成令牌数 |
| `top_p` | float | 核采样参数 |

### 图片分析参数

| 参数 | 类型 | 描述 |
|-----|------|------|
| `image_url` | string | 图片 URL 地址（必需），多个 URL 用逗号分隔 |
| `prompt` | string | 针对图片的问题或指令 |
| `image_urls` | string | 图片 URL 列表，多个用逗号分隔 |

## 本地开发

```bash
# 安装依赖
uv sync

# 运行服务
uv run python -m shuttlet_claude_opus
```

## 许可证

MIT
