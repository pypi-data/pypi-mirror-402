# Accounting Subject Analysis Method MCP Server

这是一个 MCP (Model Context Protocol) 服务器，提供根据科目/指标名称获取该科目/指标的分析方法和分析输出样例的工具。

## 功能

- **get_analysis_method**: 根据科目/指标名称获取分析方法和输出样例
- **list_all_subjects**: 列出所有可用的科目/指标名称
- **get_subject_alias**: 根据科目/指标名称获取该科目/指标的别称列表

## 安装

### 从 PyPI 安装（推荐）

包已发布到 PyPI，可以直接安装：

```bash
pip install accounting-subject-analysis-mcp-server
```

或使用 `uv`：

```bash
uv pip install accounting-subject-analysis-mcp-server
```

### 从源码安装

如果您想从源码安装或开发：

```bash
git clone <repository-url>
cd get_accounting_subject_analysis_method
pip install -e .
```

## 使用方法

### 作为 MCP 服务器运行（stdio 协议）

服务器默认使用 stdio（标准输入/输出）协议与 MCP 客户端通信。

#### 方式一：使用安装后的命令（推荐）

安装包后，可以直接使用命令：

```bash
accounting-analysis-server
```

或使用 `uv run`：

```bash
uv run accounting-analysis-server
```

#### 方式二：使用 Python 模块方式

```bash
python -m accounting_subject_analysis_mcp_server
```

或使用 `uv run`：

```bash
uv run -m accounting_subject_analysis_mcp_server
```

### 配置 MCP 客户端

在 MCP 客户端配置文件中添加此服务器。服务器支持 stdio 协议，可以通过以下方式配置：

#### 方式一：使用安装后的命令（推荐）

```json
{
  "mcpServers": {
    "accounting-subject-analysis": {
      "command": "accounting-analysis-server"
    }
  }
}
```

或使用 `uv run`：

```json
{
  "mcpServers": {
    "accounting-subject-analysis": {
      "command": "uv",
      "args": ["run", "accounting-analysis-server"]
    }
  }
}
```

#### 方式二：使用 Python 模块方式

```json
{
  "mcpServers": {
    "accounting-subject-analysis": {
      "command": "python",
      "args": ["-m", "accounting_subject_analysis_mcp_server"]
    }
  }
}
```

或使用 `uv run`：

```json
{
  "mcpServers": {
    "accounting-subject-analysis": {
      "command": "uv",
      "args": ["run", "-m", "accounting_subject_analysis_mcp_server"]
    }
  }
}
```

**注意：** 
- 使用 `uv` 命令时，需要确保已安装 `uv`。如果尚未安装，可以访问 [uv 官网](https://github.com/astral-sh/uv) 进行安装。
- 使用 `uv run` 时，`uv` 会自动管理依赖，无需手动安装包。

## 工具说明

### get_analysis_method

根据科目/指标名称获取该科目/指标的分析方法和分析输出样例。

**参数：**
- `subject_name` (string): 科目/指标名称，例如："货币资金"、"应收账款"、"存货"等

**返回：**
- 包含以下字段的字典：
  - `科目/指标名称`: 科目/指标名称
  - `分析方法`: 该科目/指标的分析方法
  - `输出样例`: 分析输出的样例

**示例：**
```python
# 查询"货币资金"的分析方法
result = get_analysis_method("货币资金")
```

### list_all_subjects

列出所有可用的科目/指标名称列表。

**返回：**
- 包含以下字段的字典：
  - `总数`: 可用科目/指标的总数
  - `科目/指标列表`: 所有科目/指标名称的列表

### get_subject_alias

根据科目/指标名称获取该科目/指标的别称列表。

**参数：**
- `subject_name` (string): 科目/指标名称，例如："应收账款"、"货币资金"、"存货"等

**返回：**
- 包含以下字段的字典：
  - `科目/指标名称`: 科目/指标名称
  - `别称`: 该科目/指标的别称列表（如果存在）
  - `提示`: 如果该科目/指标暂无别称信息，会显示提示信息

**示例：**
```python
# 查询"应收账款"的别称
result = get_subject_alias("应收账款")
```

**注意：** 如果知识库中的科目/指标条目包含 `别称` 字段，该工具会返回别称列表。别称可以是字符串（单个别称）或列表（多个别称）。如果该科目/指标没有别称信息，会返回空列表并显示提示信息。

## 知识库

知识库数据保存在 `config/kb.json` 文件中，包含各种会计科目和财务指标的分析方法和输出样例。

知识库中的每个条目可以包含以下字段：
- `科目/指标名称`: 科目/指标的标准名称（必需）
- `分析方法`: 该科目/指标的分析方法（可选）
- `输出样例`: 分析输出的样例（可选）
- `别称`: 该科目/指标的别称，可以是字符串或字符串列表（可选）

## 支持的科目/指标

服务器支持以下科目/指标（部分列表）：
- 货币资金
- 应收账款
- 存货
- 固定资产
- 短期借款
- 应付账款
- 营业收入
- 净利润
- 现金流量表
- 利润表
- 偿债能力指标
- 营运能力指标
- 盈利能力指标
- 现金偿债能力
- 增长能力指标
- 等等...

使用 `list_all_subjects` 工具可以获取完整的列表。
