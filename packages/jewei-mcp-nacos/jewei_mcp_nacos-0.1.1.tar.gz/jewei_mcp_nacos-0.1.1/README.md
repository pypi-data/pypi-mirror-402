# jewei-mcp-nacos

Nacos MCP Server - 让 AI 助手能够查询和管理 Nacos 配置。

支持 Nacos 3.x 版本。

## 快速开始

### Claude Code

在项目 `.mcp.json` 或全局 `~/.claude.json` 中添加：

```json
{
  "mcpServers": {
    "nacos": {
      "type": "stdio",
      "command": "uvx",
      "args": ["jewei-mcp-nacos"],
      "env": {
        "NACOS_HOST": "localhost",
        "NACOS_API_PORT": "8848",
        "NACOS_CONSOLE_PORT": "8080",
        "NACOS_USERNAME": "nacos",
        "NACOS_PASSWORD": "your-password",
        "NACOS_NAMESPACE": "dev"
      }
    }
  }
}
```

### Cursor

在 `~/.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "nacos": {
      "command": "uvx",
      "args": ["jewei-mcp-nacos"],
      "env": {
        "NACOS_HOST": "localhost",
        "NACOS_API_PORT": "8848",
        "NACOS_CONSOLE_PORT": "8080",
        "NACOS_USERNAME": "nacos",
        "NACOS_PASSWORD": "your-password"
      }
    }
  }
}
```

### Windsurf

在 `~/.codeium/windsurf/mcp_config.json` 中添加：

```json
{
  "mcpServers": {
    "nacos": {
      "command": "uvx",
      "args": ["jewei-mcp-nacos"],
      "env": {
        "NACOS_HOST": "localhost",
        "NACOS_API_PORT": "8848",
        "NACOS_CONSOLE_PORT": "8080"
      }
    }
  }
}
```

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "nacos": {
      "command": "uvx",
      "args": ["jewei-mcp-nacos"],
      "env": {
        "NACOS_HOST": "localhost",
        "NACOS_API_PORT": "8848",
        "NACOS_CONSOLE_PORT": "8080",
        "NACOS_USERNAME": "nacos",
        "NACOS_PASSWORD": "your-password"
      }
    }
  }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NACOS_HOST` | Nacos 服务地址 | `localhost` |
| `NACOS_API_PORT` | API 端口（用于登录） | `8848` |
| `NACOS_CONSOLE_PORT` | Console 端口（用于配置操作） | `8080` |
| `NACOS_USERNAME` | 用户名（可选） | - |
| `NACOS_PASSWORD` | 密码（可选） | - |
| `NACOS_NAMESPACE` | 默认命名空间 ID | `public` |
| `NACOS_READ_ONLY` | 只读模式，禁用发布功能 | `false` |

## 可用工具

| 工具 | 说明 |
|------|------|
| `nacos_get_config` | 获取配置内容 |
| `nacos_publish_config` | 发布/更新配置（只读模式下不可用） |

## 提示示例

配置好后，你可以这样和 AI 对话：

**查询配置：**

```
帮我获取 Nacos 中 dataId 为 "application.yaml" 的配置
```

```
查看 nacos 里 user-service.yml 的配置内容，namespace 是 dev
```

```
获取 gateway 的配置，分组是 PROD_GROUP
```

**发布配置：**

```
把下面这段配置发布到 Nacos，dataId 是 "redis.yaml"：
server:
  port: 6379
```

```
更新 user-service 的配置，把数据库端口改成 3307
```

## 只读模式

设置 `NACOS_READ_ONLY=true` 可以禁用发布功能，只允许查询配置。适合生产环境使用。

```json
{
  "env": {
    "NACOS_READ_ONLY": "true"
  }
}
```

## License

MIT
