# MCP 翻译服务

基于小牛翻译（NiuTrans）API 的 MCP Provider，提供文字翻译工具和语种目录资源，方便在 Cursor/mcp-cli 等客户端中引用。

## 快速开始

### 使用 uv 安装并启动发布版

```bash
uv tool install mcp-translation-text
```

## 环境变量

- `NIUTRANS_API_KEY`（必填）：小牛翻译开放平台提供的 API Key,可免费使用, 请登录后获取:https://niutrans.com/cloud/account_info/info

## 计费说明

本服务使用小牛翻译的文本翻译 API，计费规则如下：

| 项目 | 说明 |
|------|------|
| 计费单位 | 2000 字符 = 1 积分 |
| 免费额度 | 每天免费赠送 **100 积分** |
| 每日可翻译 | 约 **20 万字符**（免费额度） |

> 💡 **提示**：每日免费赠送的 100 积分足够日常使用，超出部分可在[小牛翻译开放平台](https://niutrans.com/price)充值购买。

## MCP 客户端配置示例

若通过 `uv tool install` 安装，可在 `mcp.json` 中写：

```json
{
  "mcpServers": {
    "translation": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "tool",
        "run",
        "mcp-translation-text"
      ],
      "env": {
        "NIUTRANS_API_KEY": "${env.NIUTRANS_API_KEY}"
      }
    }
  }
}
```

启动 Cursor 后执行 `ListTools` 即可看到 `translate_text`，同时支持 `ListResources` 读取 `language://catalog`。

## 可用功能

### 工具：`translate_text`

- **参数**：
  - `text`：待翻译内容。
  - `source`：源语言代码或别名（会通过本地映射表规范化）。
  - `target`：目标语言代码或别名。
- **返回**：
  ```json
  {
    "source": "zh",
    "target": "en",
    "original_text": "你好",
    "translated_text": "Hello",
    "raw": { ... 小牛原始响应 ... }
  }
  ```

### 资源：`language://catalog`

提供所有可用语种及别名，示例如下：

```json
{
  "total": 455,
  "languages": [
    {"code": "zh", "zh": "中文(简体)", "en": "Chinese (Simplified)"},
    {"code": "en", "zh": "英语", "en": "English"}
    // ... 其余省略 ...
  ],
  "aliases": {
    "zhongwenjianti": "zh",
    "english": "en"
    // ... 其余省略 ...
  }
}
```

推荐在客户端的 LLM 中先读取该资源，完成语种描述到代码的映射后，再调用 `translate_text`。

## 调试与常见问题

- **缺少 API Key**：启动时报 `缺少环境变量 NIUTRANS_API_KEY`，请确认已在 `.env` 或系统环境中设置。
- **语种不支持**：`translate_text` 会校验语种代码/别名，若报错请检查是否使用了 `language://catalog` 中列出的值。
- **路径或依赖问题**：脚本依赖 `uv`，请先安装 `pip install uv` 或参考 [uv 文档](https://github.com/astral-sh/uv)。
- **命令名称**：通过 PyPI 安装后，可直接运行 `mcp-translation-text`；若 global PATH 中找不到，记得激活虚拟环境或使用 `python -m mcp_translation_text`。
- **发布/升级包**：
  ```bash
  python -m build
  twine upload dist/*
  ```

## 目录结构（关键文件）

```
E:\MCP
├── pyproject.toml
├── server.py                # 入口包装，确保 python server.py 可运行
├── src/
│   └── translation_server.py
├── scripts/
│   ├── start.ps1
│   └── start.sh
├── .env.example
├── LICENSE
└── README.md
```

发布后，用户只需设置 NiuTrans API Key，即可通过 `mcp-translation-text` 直接加载该 Provider。

