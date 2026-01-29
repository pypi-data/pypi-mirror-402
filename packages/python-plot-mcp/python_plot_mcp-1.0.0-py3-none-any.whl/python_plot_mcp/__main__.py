#!/usr/bin/env python3
"""python-plot-mcp 命令行入口点

支持 uvx 直接运行: uvx python-plot-mcp
"""

from python_plot_mcp.server import main


def entry_point() -> None:
    """uvx 入口点"""
    main()


if __name__ == "__main__":
    entry_point()
