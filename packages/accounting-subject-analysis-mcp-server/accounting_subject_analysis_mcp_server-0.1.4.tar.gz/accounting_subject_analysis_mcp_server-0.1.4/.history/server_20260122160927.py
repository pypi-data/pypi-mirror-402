#!/usr/bin/env python3
"""
MCP Server for Accounting Subject Analysis Method
提供根据科目/指标名称获取分析方法和输出样例的工具
"""

import json
from pathlib import Path

from fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP("Accounting Subject Analysis Method Server")

# 获取知识库文件路径
KB_FILE = Path(__file__).parent / "config" / "kb.json"

# 加载知识库数据
def load_knowledge_base() -> dict:
    """加载知识库数据"""
    if not KB_FILE.exists():
        raise FileNotFoundError(f"知识库文件不存在: {KB_FILE}")
    
    with open(KB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# 全局变量存储知识库数据
_kb_data = None

def get_kb_data() -> dict:
    """获取知识库数据（懒加载）"""
    global _kb_data
    if _kb_data is None:
        _kb_data = load_knowledge_base()
    return _kb_data

@mcp.tool
def get_analysis_method(subject_name: str) -> dict:
    """
    根据科目/指标名称获取分析方法和分析输出样例
    
    Args:
        subject_name: 科目/指标名称，例如："应收账款"、"货币资金"、"存货"等
    
    Returns:
        包含分析方法和输出样例的字典，如果未找到则返回错误信息
    """
    try:
        kb_data = get_kb_data()
        entries = kb_data.get("entries", [])
        
        # 查找匹配的科目/指标
        for entry in entries:
            if entry.get("科目/指标名称") == subject_name:
                result = {
                    "科目/指标名称": entry.get("科目/指标名称"),
                    "分析方法": entry.get("分析方法", ""),
                    "输出样例": entry.get("输出样例", "")
                }
                return result
        
        # 如果未找到精确匹配，尝试模糊匹配
        matched_entries = []
        for entry in entries:
            name = entry.get("科目/指标名称", "")
            if subject_name in name or name in subject_name:
                matched_entries.append(name)
        
        if matched_entries:
            return {
                "error": f"未找到精确匹配的科目/指标 '{subject_name}'",
                "建议": f"您是否想查找以下相关科目/指标: {', '.join(matched_entries)}"
            }
        
        # 列出所有可用的科目/指标
        all_subjects = [entry.get("科目/指标名称") for entry in entries if entry.get("科目/指标名称")]
        return {
            "error": f"未找到科目/指标 '{subject_name}'",
            "可用科目/指标列表": all_subjects
        }
    
    except FileNotFoundError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"处理请求时发生错误: {str(e)}"}

@mcp.tool
def list_all_subjects() -> dict:
    """
    列出所有可用的科目/指标名称列表
    
    Returns:
        包含所有科目/指标名称的字典
    """
    try:
        kb_data = get_kb_data()
        entries = kb_data.get("entries", [])
        subjects = [entry.get("科目/指标名称") for entry in entries if entry.get("科目/指标名称")]
        
        return {
            "总数": len(subjects),
            "科目/指标列表": subjects
        }
    except Exception as e:
        return {"error": f"获取科目/指标列表时发生错误: {str(e)}"}

def main():
    """MCP 服务器主入口函数"""
    # 运行 MCP 服务器，默认使用 stdio 传输方式
    mcp.run()

if __name__ == "__main__":
    main()
