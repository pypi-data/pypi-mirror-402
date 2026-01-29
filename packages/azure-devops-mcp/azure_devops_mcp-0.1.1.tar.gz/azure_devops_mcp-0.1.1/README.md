# Azure DevOps MCP Server

一个用于连接 Azure DevOps / TFS 的 MCP (Model Context Protocol) 服务，支持查询和创建工作项。

## 功能特性

- **查询工作项**: 通过 ID、WIQL 查询语句或文本搜索获取工作项
- **创建工作项**: 支持 Bug、Task、User Story 等多种工作项类型
- **获取项目列表**: 列出组织中的所有项目
- **获取工作项类型**: 查看项目中可用的工工作项类型

## 安装

### 1. 克隆或下载此项目

```bash
cd azure-devops-mcp
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 pip (开发模式):

```bash
pip install -e .
```

## 配置

### 方式一: 使用配置文件 (推荐)

编辑 `config.yaml` 文件:

```yaml
organization:
  url: "https://dev.azure.com/your-organization"
  project: "your-project-name"

auth:
  method: "oauth"
  oauth:
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    tenant_id: "your-tenant-id"
```

### 方式二: 使用环境变量

复制 `.env.example` 到 `.env`:

```bash
cp .env.example .env
```

然后编辑 `.env` 文件:

```bash
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization
AZURE_DEVOPS_PROJECT=your-project-name

AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

## Azure AD 应用注册配置

要使用 OAuth 2.0 / Service Principal 认证，需要先在 Azure AD 中注册应用:

### 1. 注册 Azure AD 应用

1. 访问 [Azure Portal](https://portal.azure.com/)
2. 导航到 **Azure Active Directory** > **App registrations**
3. 点击 **New registration**
4. 输入应用名称 (如 "Azure DevOps MCP")
5. 选择支持的账户类型
6. 点击 **Register**

### 2. 获取认证信息

在应用注册页面:

1. 记录 **Application (client) ID** → `AZURE_CLIENT_ID`
2. 记录 **Directory (tenant) ID** → `AZURE_TENANT_ID`
3. 导航到 **Certificates & secrets** > **Client secrets**
4. 点击 **New client secret**
5. 输入描述并选择过期时间
6. 记录生成的 **Value** → `AZURE_CLIENT_SECRET`

### 3. 配置 API 权限

1. 在应用注册页面，导航到 **API permissions**
2. 点击 **Add a permission**
3. 选择 **APIs my organization uses**
4. 搜索并选择 **Azure DevOps**
5. 选择权限:
   - **vso.work** (读取和管理工作项)
   - **vso.work_write** (创建和修改工作项)
6. 点击 **Add permissions**
7. 点击 **Grant admin consent** for your organization

## 使用方法

### 在 Claude Desktop 中配置

编辑 Claude Desktop 配置文件:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

添加以下配置:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": [
        "/path/to/azure-devops-mcp/src/server.py"
      ],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/your-organization",
        "AZURE_DEVOPS_PROJECT": "your-project-name",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret",
        "AZURE_TENANT_ID": "your-tenant-id"
      }
    }
  }
}
```

### 重启 Claude Desktop

配置完成后，重启 Claude Desktop 以加载 MCP 服务。

## 可用工具

### 1. get_work_item
获取单个工作项详情

```
输入: work_item_id (必需), project (可选)
```

### 2. get_work_items
批量获取多个工作项

```
输入: work_item_ids (必需), fields (可选), project (可选)
```

### 3. query_work_items
使用 WIQL 查询工作项

```
输入: wiql (必需), project (可选)

示例 WIQL:
SELECT [System.Id] FROM WorkItems
WHERE [System.TeamProject] = @project
AND [System.State] = 'Active'
```

### 4. create_work_item
创建新工作项

```
输入: work_item_type (必需), title (必需),
      description (可选), assigned_to (可选),
      fields (可选), project (可选)
```

### 5. search_work_items
搜索工作项

```
输入: search_text (必需), project (可选), top (可选)
```

### 6. get_projects
获取所有项目列表

### 7. get_work_item_types
获取可用的工工作项类型

```
输入: project (可选)
```

## 使用示例

### 查询工作项

```
帮我查询 ID 为 12345 的工作项详情
```

### 搜索工作项

```
搜索标题中包含 "登录" 的工作项
```

### 创建工作项

```
创建一个 Bug:
标题: 用户登录时出现错误
描述: 在用户登录页面输入密码后点击登录按钮，系统返回 500 错误
指派给: zhangsan@example.com
优先级: 1
```

### WIQL 查询

```
使用 WIQL 查询所有分配给我的高优先级 Bug
```

## 故障排除

### 认证失败

- 确认 Client Secret 没有过期
- 确认已授予 API 权限并执行了 Admin Consent
- 检查 Tenant ID、Client ID 是否正确

### 401 Unauthorized

- 检查 API 权限是否正确配置
- 确认已授予 Admin Consent
- 确认应用有权访问指定的 Azure DevOps 组织

### 找不到项目

- 确认项目名称拼写正确
- 确认你的账户有访问该项目的权限
- 尝试使用 `get_projects` 工具列出所有可用项目

## 开发

### 项目结构

```
azure-devops-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP 服务器主文件
│   └── azure_devops_client.py # Azure DevOps API 客户端
├── config.yaml                # 配置文件
├── .env.example              # 环境变量示例
├── requirements.txt          # Python 依赖
├── pyproject.toml           # 项目配置
└── README.md                # 本文件
```

### 运行测试

```bash
python src/server.py
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 相关链接

- [MCP 协议文档](https://modelcontextprotocol.io/)
- [Azure DevOps REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [Azure AD 应用注册](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
