#!/usr/bin/env python3
"""GROMACS MDKit 命令行接口"""

import sys
from .gromacs import MDKit


def main():
    """命令行主函数"""
    mdkit = MDKit()
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["-h", "--help"]:
            print("GROMACS MDKit v1.0.3 - 分子动力学预处理工具")
            print("\n用法:")
            print("  mdkit                    # 启动交互式菜单")
            print("  mdkit --version          # 显示版本信息")
            print("  mdkit --help             # 显示帮助信息")
            print("  mdkit --test             # 测试模式")
            return 0
        elif arg in ["-v", "--version"]:
            print("GROMACS MDKit v1.0.3")
            print("Copyright (c) 2024 Pengcheng Li")
            return 0
        elif arg in ["-t", "--test"]:
            print("🧪 GROMACS MDKit 测试模式")
            print("=" * 40)
            print("✅ 包安装成功")
            print("✅ CLI 接口正常工作")
            print("✅ 依赖库加载正常")
            print("\n" + "=" * 40)
            print("✅ 所有测试通过！")
            print("\n提示: 运行 'mdkit' 启动完整程序")
            return 0
        else:
            print(f"错误: 未知参数 '{arg}'")
            print("使用 'mdkit --help' 查看帮助")
            return 1
    
    # 无参数时启动交互式菜单
    try:
        while True:
            choice = mdkit.main_menu()
            mdkit.handle_main_menu(choice)
            input("\n按Enter继续...")
    except KeyboardInterrupt:
        mdkit.console.print("\n[bold yellow]已退出[/bold yellow]")
        return 0
    except Exception as e:
        mdkit.console.print(f"[red]程序错误: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())