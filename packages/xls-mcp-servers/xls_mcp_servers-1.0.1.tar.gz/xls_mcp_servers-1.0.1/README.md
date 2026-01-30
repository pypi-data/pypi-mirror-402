# MCP XLS Server

支持读取和写入 `.xls` 格式（Excel 97-2003 二进制格式）的 MCP 服务器。

## 功能特性

- ✅ 读取 `.xls` 文件数据
- ✅ 写入数据到 `.xls` 文件
- ✅ 创建新的 `.xls` 文件
- ✅ 更新指定单元格的值
- ✅ 列出文件中的所有工作表
- ✅ 获取文件元数据信息

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install xls-mcp-servers
```

### 使用 uvx 运行（无需安装）

```bash
uvx xls-mcp-servers
```

### 从源码安装

1. 克隆仓库：

```bash
git clone https://github.com/Lincyghb/xls-mcp-server.git
cd xls-mcp-server
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 配置 MCP 客户端

### Cursor 配置

在 Cursor 的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "xls-mcp-servers": {
      "command": "xls-mcp-servers"
    }
  }
}
```

或者如果从源码运行：

```json
{
  "mcpServers": {
    "xls-mcp-servers": {
      "command": "python",
      "args": ["/path/to/xls-mcp-servers/server.py"],
      "cwd": "/path/to/xls-mcp-servers"
    }
  }
}
```

**注意：** 
- 如果使用 `pip install` 安装，路径应为 Python 包安装位置
- 如果使用 `uvx` 运行，无需配置路径，直接使用包名即可
- 如果从源码运行，请将路径 `/path/to/xls-mcp-servers` 替换为你的实际路径（Windows 用户使用 `C:/path/to/xls-mcp-servers` 格式）

### 路径配置

如果需要限制服务器可以访问的文件路径，可以在 `server.py` 中修改 `ALLOWED_PATHS` 列表：

```python
ALLOWED_PATHS = [
    "/path/to/data",           # Linux/Mac 示例
    "C:/path/to/data"          # Windows 示例
]
```

如果 `ALLOWED_PATHS` 为空列表，则允许访问所有路径。

## 可用工具

### 1. read_xls - 读取 Excel 文件

读取 `.xls` 文件的数据。

**参数：**
- `filepath` (必需): Excel 文件路径
- `sheet_name` (可选): 工作表名称，默认读取第一个工作表
- `start_row` (可选): 起始行号（0-based）
- `end_row` (可选): 结束行号（0-based）
- `start_col` (可选): 起始列号（0-based）
- `end_col` (可选): 结束列号（0-based）

**示例：**
```json
{
  "filepath": "/path/to/example.xls",
  "sheet_name": "Sheet1",
  "start_row": 0,
  "end_row": 10
}
```

### 2. write_xls - 写入数据到 Excel 文件

写入数据到 `.xls` 文件。

**参数：**
- `filepath` (必需): Excel 文件路径
- `sheet_name` (必需): 工作表名称
- `data` (必需): 二维数组数据
- `start_cell` (可选): 起始单元格（如 "A1"），默认为 "A1"
- `overwrite` (可选): 是否覆盖现有文件，默认为 false（追加模式）

**示例：**
```json
{
  "filepath": "/path/to/test.xls",
  "sheet_name": "Sheet1",
  "data": [
    ["ID", "PATH", "NAME"],
    [1001, "A/B", "张三"]
  ],
  "start_cell": "A1"
}
```

### 3. list_sheets_xls - 列出工作表

列出 `.xls` 文件中的所有工作表名称。

**参数：**
- `filepath` (必需): Excel 文件路径

**示例：**
```json
{
  "filepath": "/path/to/example.xls"
}
```

### 4. create_xls - 创建新的 Excel 文件

创建新的 `.xls` 文件。

**参数：**
- `filepath` (必需): 要创建的文件路径
- `sheet_name` (可选): 工作表名称，默认为 "Sheet1"
- `data` (可选): 初始数据（二维数组）

**示例：**
```json
{
  "filepath": "/path/to/new_file.xls",
  "sheet_name": "Sheet1",
  "data": [
    ["列1", "列2", "列3"],
    ["值1", "值2", "值3"]
  ]
}
```

### 5. get_xls_metadata - 获取文件元数据

获取 `.xls` 文件的元数据信息。

**参数：**
- `filepath` (必需): Excel 文件路径

**示例：**
```json
{
  "filepath": "/path/to/example.xls"
}
```

### 6. update_xls_cell - 更新单元格

更新 `.xls` 文件中指定单元格的值。

**参数：**
- `filepath` (必需): Excel 文件路径
- `sheet_name` (必需): 工作表名称
- `cell` (必需): 单元格地址（如 "A1"）
- `value` (必需): 要设置的值

**示例：**
```json
{
  "filepath": "/path/to/test.xls",
  "sheet_name": "Sheet1",
  "cell": "A1",
  "value": "新值"
}
```

## 使用示例

### 读取 NPC 配置表

```python
# 通过 MCP 调用
read_xls(
    filepath="/path/to/config.xls",
    sheet_name="Sheet1"
)
```

### 创建新的配置

```python
# 通过 MCP 调用
write_xls(
    filepath="/path/to/config.xls",
    sheet_name="Sheet1",
    data=[
        [1001, "示例数据1", "示例数据2", 331, 331, "示例名称", 0, 15, 0]
    ],
    start_cell="A2"  # 从第2行开始写入（第1行可能是表头）
)
```

## 技术说明

### 使用的库

- **xlrd**: 用于读取 `.xls` 文件
- **xlwt**: 用于写入 `.xls` 文件
- **xlutils**: 用于复制和修改现有的 `.xls` 文件
- **mcp**: MCP SDK，用于实现 MCP 协议

### 限制

1. **只支持 `.xls` 格式**：不支持 `.xlsx` 格式（需要使用其他 MCP 服务器）
2. **日期处理**：日期会被转换为字符串格式（YYYY-MM-DD）
3. **格式保留**：使用 `xlutils.copy` 时，会尽量保留原有格式，但某些复杂格式可能无法完全保留

## 故障排除

### 1. 文件路径错误

确保使用绝对路径，并且路径中的反斜杠需要转义或使用正斜杠。

### 2. 权限错误

确保对目标目录有读写权限。

### 3. 文件被占用

如果文件正在被 Excel 或其他程序打开，写入操作会失败。请先关闭文件。

### 4. 工作表不存在

使用 `list_sheets_xls` 先查看文件中有哪些工作表。

## 更新日志

- 2026-01-22: 初始版本，支持基本的读写功能
