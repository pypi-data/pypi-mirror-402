# AigoHotel MCP Server (UV Version)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-MCP%20Server-green.svg)](https://github.com/jlowin/fastmcp)

AIGOHOTEL 酒店搜索 MCP Server。通过标准的 Model Context Protocol (MCP) 协议为 AI 助手提供全球酒店搜索能力。

本项目使用 `uv` 进行依赖管理和环境隔离。

## 项目结构

```
aigohotel-mcp-uv/
├── README.md
├── pyproject.toml
├── server.py
├── aigohotel_mcp/
│   ├── __init__.py
│   └── server.py
└── uv.lock
```

## 工具列表

**search_hotels** - 查询全球酒店信息
- 支持按城市、景点、酒店、交通枢纽等多种地点类型搜索
- 支持星级筛选、距离筛选、入住日期等多维度条件
- 返回符合条件的酒店列表(JSON格式)

### 请求参数

**必填参数**:
- **place** (string): 目的地(城市、景点、酒店、交通枢纽、地标等)
- **placeType** (string): 目的地类型(城市、区/县、机场、火车站、酒店、景点等)

**可选参数**:
- **originalQuery** (string): 用户的原始问询句
- **checkIn** (string): 入住日期,格式 yyyy-MM-dd,默认次日
- **stayNights** (int): 入住晚数,默认 1
- **starRatings** (array): 酒店星级范围,如 [4.5, 5.0],默认 [0.0, 5.0]
- **adultCount** (int): 每间房成人数量,默认 2
- **distanceInMeter** (int): 距离景点的米数,默认 5000
- **size** (int): 返回结果数量,默认 10,最大 20
- **withHotelAmenities** (bool): 是否包含酒店设施,默认 true
- **withRoomAmenities** (bool): 是否包含客房设施,默认 true
- **language** (string): 语言环境(zh_CN, en_US等),默认 zh_CN
- **queryParsing** (bool): 是否分析用户个性化需求,默认 true

### 使用示例

**示例 1**: 搜索西雅图的酒店
```json
{
  "place": "西雅图",
  "placeType": "城市"
}
```

**示例 2**: 搜索白金汉宫附近的高星级酒店
```json
{
  "place": "白金汉宫",
  "placeType": "景点",
  "checkIn": "2026-01-01",
  "starRatings": [4.5, 5.0]
}
```

## 快速开始

### 1. 初始化项目

```bash
# 进入项目目录
cd aigohotel-mcp-uv

# 初始化 uv 项目(如果是新克隆的项目)
uv init

# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
uv add fastmcp httpx
```

### 2. 配置 API Key (必需)

**获取 API Key**: https://mcp.agentichotel.cn/apply

设置环境变量:

```bash
# Windows PowerShell:
$env:AIGOHOTEL_API_KEY="mcp_your_actual_api_key_here"

# Windows CMD:
set AIGOHOTEL_API_KEY=mcp_your_actual_api_key_here

# Linux/Mac:
export AIGOHOTEL_API_KEY=mcp_your_actual_api_key_here
```

> **重要**: 
> - 前往 https://mcp.agentichotel.cn/apply 申请 API Key
> - API Key 必须以 `mcp_` 开头
> - 未配置或格式错误将导致 API 请求失败

### 3. 启动服务器

```bash
# 方式1: 直接运行
python server.py

# 方式2: 使用 uvx 启动
uvx aigohotel_mcp

# 方式3: 使用 uv run
uv run python server.py
```

启动成功后会显示:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

如果 API Key 格式错误,会显示警告:
```
警告: API Key 格式错误,应以 'mcp_' 开头
```

## MCP 客户端配置

### 方式1: UVX 命令行模式 (推荐)

在 MCP 客户端配置文件中添加:

**Claude Desktop (Windows)**:
配置文件路径: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aigohotel": {
      "command": "uvx",
      "args": [
        "--from",
        "e:/Cursor/测试脚本File/aigohotel-mcp-uv",
        "aigohotel_mcp"
      ],
      "env": {
        "AIGOHOTEL_API_KEY": "mcp_your_actual_api_key_here"
      }
    }
  }
}
```

**Claude Desktop (Mac/Linux)**:
配置文件路径: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aigohotel": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/aigohotel-mcp-uv",
        "aigohotel_mcp"
      ],
      "env": {
        "AIGOHOTEL_API_KEY": "mcp_your_actual_api_key_here"
      }
    }
  }
}
```

**Cline/其他 MCP 客户端**:
```json
{
  "mcpServers": {
    "aigohotel": {
      "command": "uvx",
      "args": ["--from", "e:/Cursor/测试脚本File/aigohotel-mcp-uv", "aigohotel_mcp"],
      "env": {
        "AIGOHOTEL_API_KEY": "mcp_your_actual_api_key_here"
      }
    }
  }
}
```

### 方式2: HTTP 服务模式

先手动启动服务:
```bash
cd aigohotel-mcp-uv
python server.py
```

然后在 MCP 配置文件中添加:
```json
{
  "mcpServers": {
    "aigohotel": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 配置说明

- **command**: 使用 `uvx` 命令启动
- **args**: 
  - `--from`: 指定项目路径(绝对路径)
  - `aigohotel_mcp`: 项目入口脚本名称(在 pyproject.toml 中定义)
- **env**: 环境变量配置
  - `AIGOHOTEL_API_KEY`: 必须配置,从 https://mcp.agentichotel.cn/apply 获取

## 开发指南

### 安装开发依赖

```bash
uv add --dev pytest pytest-asyncio
```

### 运行测试

```bash
uv run pytest
```

## API 鉴权说明

访问 https://mcp.agentichotel.cn/apply 申请 API Key

## 许可证

本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情。

## 相关链接
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [API Key 申请](https://mcp.agentichotel.cn/apply)
