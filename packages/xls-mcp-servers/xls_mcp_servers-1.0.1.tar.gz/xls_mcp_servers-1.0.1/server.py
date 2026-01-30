#!/usr/bin/env python3
"""
MCP Server for reading and writing .xls Excel files
Supports legacy Excel 97-2003 binary format (.xls)
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)

import xlrd
import xlwt
from xlutils.copy import copy as xlutils_copy

# 创建 MCP 服务器实例
server = Server("xls-excel-server")

# 允许访问的文件路径白名单（可根据需要配置）
ALLOWED_PATHS = []


def is_path_allowed(filepath: str) -> bool:
    """检查文件路径是否在允许列表中"""
    if not ALLOWED_PATHS:
        return True  # 如果没有配置白名单，允许所有路径
    
    abs_path = os.path.abspath(filepath)
    for allowed in ALLOWED_PATHS:
        if abs_path.startswith(os.path.abspath(allowed)):
            return True
    return False


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="read_xls",
            description="读取 .xls Excel 文件的数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Excel 文件路径（.xls 格式）"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "工作表名称（可选，默认读取第一个工作表）"
                    },
                    "start_row": {
                        "type": "integer",
                        "description": "起始行号（0-based，可选）"
                    },
                    "end_row": {
                        "type": "integer",
                        "description": "结束行号（0-based，可选）"
                    },
                    "start_col": {
                        "type": "integer",
                        "description": "起始列号（0-based，可选）"
                    },
                    "end_col": {
                        "type": "integer",
                        "description": "结束列号（0-based，可选）"
                    }
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="write_xls",
            description="写入数据到 .xls Excel 文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Excel 文件路径（.xls 格式）"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "工作表名称（如果不存在则创建）"
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {}
                        },
                        "description": "要写入的数据（二维数组，每行是一个数组）"
                    },
                    "start_cell": {
                        "type": "string",
                        "description": "起始单元格（如 'A1'，可选，默认为 A1）"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "是否覆盖现有文件（默认 false，追加模式）"
                    }
                },
                "required": ["filepath", "sheet_name", "data"]
            }
        ),
        Tool(
            name="list_sheets_xls",
            description="列出 .xls 文件中的所有工作表名称",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Excel 文件路径（.xls 格式）"
                    }
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="create_xls",
            description="创建新的 .xls Excel 文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "要创建的 Excel 文件路径（.xls 格式）"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "工作表名称（可选，默认为 Sheet1）"
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {}
                        },
                        "description": "初始数据（二维数组，可选）"
                    }
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="get_xls_metadata",
            description="获取 .xls 文件的元数据信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Excel 文件路径（.xls 格式）"
                    }
                },
                "required": ["filepath"]
            }
        ),
        Tool(
            name="update_xls_cell",
            description="更新 .xls 文件中指定单元格的值",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Excel 文件路径（.xls 格式）"
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "工作表名称"
                    },
                    "cell": {
                        "type": "string",
                        "description": "单元格地址（如 'A1'）"
                    },
                    "value": {
                        "description": "要设置的值（字符串、数字等）"
                    }
                },
                "required": ["filepath", "sheet_name", "cell", "value"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""
    
    if name == "read_xls":
        filepath = arguments["filepath"]
        sheet_name = arguments.get("sheet_name")
        start_row = arguments.get("start_row")
        end_row = arguments.get("end_row")
        start_col = arguments.get("start_col")
        end_col = arguments.get("end_col")
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not os.path.exists(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            workbook = xlrd.open_workbook(filepath)
            
            if sheet_name:
                try:
                    sheet = workbook.sheet_by_name(sheet_name)
                except xlrd.XLRDError:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": f"工作表 '{sheet_name}' 不存在"}, ensure_ascii=False)
                    )]
            else:
                sheet = workbook.sheet_by_index(0)
            
            # 确定读取范围
            row_start = start_row if start_row is not None else 0
            row_end = end_row + 1 if end_row is not None else sheet.nrows
            col_start = start_col if start_col is not None else 0
            col_end = end_col + 1 if end_col is not None else sheet.ncols
            
            # 读取数据
            data = []
            for row_idx in range(row_start, min(row_end, sheet.nrows)):
                row = []
                for col_idx in range(col_start, min(col_end, sheet.ncols)):
                    cell_value = sheet.cell_value(row_idx, col_idx)
                    # 处理日期类型
                    if sheet.cell_type(row_idx, col_idx) == xlrd.XL_CELL_DATE:
                        date_tuple = xlrd.xldate_as_tuple(cell_value, workbook.datemode)
                        cell_value = f"{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                    row.append(cell_value)
                data.append(row)
            
            result = {
                "filepath": filepath,
                "sheet_name": sheet.name,
                "rows": len(data),
                "cols": len(data[0]) if data else 0,
                "data": data
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"读取文件失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    elif name == "write_xls":
        filepath = arguments["filepath"]
        sheet_name = arguments["sheet_name"]
        data = arguments["data"]
        start_cell = arguments.get("start_cell", "A1")
        overwrite = arguments.get("overwrite", False)
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            # 解析起始单元格
            col_letter = ''.join(filter(str.isalpha, start_cell))
            row_num = int(''.join(filter(str.isdigit, start_cell))) - 1
            
            # 将列字母转换为数字（A=0, B=1, ...）
            col_num = 0
            for char in col_letter:
                col_num = col_num * 26 + (ord(char.upper()) - ord('A') + 1)
            col_num -= 1
            
            # 如果文件存在且不覆盖，则读取现有文件
            if os.path.exists(filepath) and not overwrite:
                try:
                    old_workbook = xlrd.open_workbook(filepath, formatting_info=True)
                    workbook = xlutils_copy(old_workbook)
                except:
                    # 如果无法读取格式信息，则使用基本模式
                    old_workbook = xlrd.open_workbook(filepath, formatting_info=False)
                    workbook = xlutils_copy(old_workbook)
                
                # 获取或创建工作表
                try:
                    sheet = workbook.get_sheet(sheet_name)
                except:
                    sheet = workbook.add_sheet(sheet_name)
            else:
                # 创建新工作簿
                workbook = xlwt.Workbook()
                sheet = workbook.add_sheet(sheet_name)
            
            # 写入数据
            for row_idx, row_data in enumerate(data):
                for col_idx, cell_value in enumerate(row_data):
                    sheet.write(row_num + row_idx, col_num + col_idx, cell_value)
            
            # 保存文件
            workbook.save(filepath)
            
            result = {
                "success": True,
                "filepath": filepath,
                "sheet_name": sheet_name,
                "rows_written": len(data),
                "start_cell": start_cell
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"写入文件失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    elif name == "list_sheets_xls":
        filepath = arguments["filepath"]
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not os.path.exists(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            workbook = xlrd.open_workbook(filepath)
            sheets = workbook.sheet_names()
            
            result = {
                "filepath": filepath,
                "sheets": sheets,
                "count": len(sheets)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"读取文件失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    elif name == "create_xls":
        filepath = arguments["filepath"]
        sheet_name = arguments.get("sheet_name", "Sheet1")
        data = arguments.get("data", [])
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet(sheet_name)
            
            # 写入初始数据
            for row_idx, row_data in enumerate(data):
                for col_idx, cell_value in enumerate(row_data):
                    sheet.write(row_idx, col_idx, cell_value)
            
            workbook.save(filepath)
            
            result = {
                "success": True,
                "filepath": filepath,
                "sheet_name": sheet_name,
                "rows": len(data)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"创建文件失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    elif name == "get_xls_metadata":
        filepath = arguments["filepath"]
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not os.path.exists(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            workbook = xlrd.open_workbook(filepath)
            file_size = os.path.getsize(filepath)
            
            sheets_info = []
            for sheet in workbook.sheets():
                sheets_info.append({
                    "name": sheet.name,
                    "rows": sheet.nrows,
                    "cols": sheet.ncols
                })
            
            result = {
                "filepath": filepath,
                "file_size": file_size,
                "sheet_count": len(sheets_info),
                "sheets": sheets_info
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"读取文件失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    elif name == "update_xls_cell":
        filepath = arguments["filepath"]
        sheet_name = arguments["sheet_name"]
        cell = arguments["cell"]
        value = arguments["value"]
        
        if not is_path_allowed(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "文件路径不在允许列表中"}, ensure_ascii=False)
            )]
        
        if not os.path.exists(filepath):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"文件不存在: {filepath}"}, ensure_ascii=False)
            )]
        
        if not filepath.lower().endswith('.xls'):
            return [TextContent(
                type="text",
                text=json.dumps({"error": "只支持 .xls 格式文件"}, ensure_ascii=False)
            )]
        
        try:
            # 解析单元格地址
            col_letter = ''.join(filter(str.isalpha, cell))
            row_num = int(''.join(filter(str.isdigit, cell))) - 1
            
            # 将列字母转换为数字
            col_num = 0
            for char in col_letter:
                col_num = col_num * 26 + (ord(char.upper()) - ord('A') + 1)
            col_num -= 1
            
            # 读取现有文件
            old_workbook = xlrd.open_workbook(filepath, formatting_info=True)
            workbook = xlutils_copy(old_workbook)
            
            # 获取工作表
            try:
                sheet = workbook.get_sheet(sheet_name)
            except:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"工作表 '{sheet_name}' 不存在"}, ensure_ascii=False)
                )]
            
            # 更新单元格
            sheet.write(row_num, col_num, value)
            
            # 保存文件
            workbook.save(filepath)
            
            result = {
                "success": True,
                "filepath": filepath,
                "sheet_name": sheet_name,
                "cell": cell,
                "value": value
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"更新单元格失败: {str(e)}"}, ensure_ascii=False)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        )]


async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli_main():
    """命令行入口点（同步包装函数）"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
