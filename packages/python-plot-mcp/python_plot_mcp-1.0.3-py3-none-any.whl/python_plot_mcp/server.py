"""Python Plot MCP Server - 底层Server API实现

安全的 Python 代码执行环境，支持 matplotlib 可视化
"""

import asyncio
import base64
import glob
import os
import subprocess
import tempfile
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建 MCP 服务器实例
server = Server("python-plot-mcp")

# Python 预处理代码：配置 matplotlib 和重写 plt.show()
_PRELUDE = r"""
import os
import glob

# 设置 matplotlib 使用非交互式后端
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 重写 plt.show() 为保存图片函数
def __mcp_show(*args, **kwargs):
    fname = f"mcp_plot_{len(glob.glob('mcp_plot_*.png'))+1}.png"
    plt.savefig(fname, dpi=200, bbox_inches="tight")

plt.show = __mcp_show
"""


def execute_python_code(code: str, timeout_s: int = 12) -> dict:
    """执行Python代码并生成图表

    Args:
        code: Python 代码字符串
        timeout_s: 超时时间（秒），默认 12

    Returns:
        dict: 包含执行状态和渲染的 Markdown 输出
    """
    with tempfile.TemporaryDirectory(prefix="mcp_py_") as td:
        script_path = os.path.join(td, "main.py")

        # 写入 Python 脚本
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(_PRELUDE + "\n\n" + code + "\n")

        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            # 执行 Python 脚本
            p = subprocess.run(
                ["python", script_path],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "render_markdown": f"❌ **执行超时**（超过 {timeout_s} 秒）"
            }

        # 收集输出
        stdout = p.stdout or ""
        stderr = p.stderr or ""
        pngs = sorted(glob.glob(os.path.join(td, "*.png")))

        # 构建 Markdown 输出
        md_parts = []
        if stdout.strip():
            md_parts.append("**标准输出:**\n```\n" + stdout.strip() + "\n```")
        if stderr.strip():
            md_parts.append("**错误输出:**\n```\n" + stderr.strip() + "\n```")

        # 添加生成的图片
        for fp in pngs:
            with open(fp, "rb") as imgf:
                b64 = base64.b64encode(imgf.read()).decode("ascii")
            md_parts.append(f"![图表](data:image/png;base64,{b64})")

        markdown_output = "\n\n".join(md_parts) if md_parts else "(无输出)"

        return {
            "ok": (p.returncode == 0),
            "render_markdown": markdown_output
        }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [Tool(
        name="run_python",
        description="执行 Python 代码并生成 matplotlib 可视化图表",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码"
                },
                "timeout_s": {
                    "type": "integer",
                    "description": "超时时间（秒），默认 12",
                    "default": 12
                }
            },
            "required": ["code"]
        }
    )]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """调用工具"""
    if name == "run_python":
        result = execute_python_code(
            arguments["code"],
            arguments.get("timeout_s", 12)
        )
        return [TextContent(type="text", text=result["render_markdown"])]
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """启动MCP服务器"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
