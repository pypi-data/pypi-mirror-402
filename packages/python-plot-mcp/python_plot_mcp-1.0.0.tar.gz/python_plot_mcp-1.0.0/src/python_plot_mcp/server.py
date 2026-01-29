"""Python Plot MCP Server - STDIO 模式

安全的 Python 代码执行环境，支持 matplotlib 可视化
"""

import base64
import glob
import os
import subprocess
import tempfile
from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例
mcp = FastMCP("Python Plot MCP", json_response=True)

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


@mcp.tool()
def run_python(code: str, timeout_s: int = 12) -> dict:
    """执行 Python 代码并生成 matplotlib 图表

    Args:
        code: Python 代码字符串
        timeout_s: 超时时间（秒），默认 12

    Returns:
        dict: 包含执行状态和渲染的 Markdown 输出
        {
            "ok": bool,  # 是否执行成功
            "render_markdown": str  # Markdown 格式的输出（包含图片）
        }
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


def main() -> None:
    """启动 MCP 服务器（STDIO 模式）"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
