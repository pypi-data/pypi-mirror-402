#!/usr/bin/env python
'''
锐派(rypi) 是由锐白开发的派神(python)工具包，包含多种网络工具和实用程序模块。
'''

VER = r'''
rypi version: 2026.1.18.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] - rymaa_cn@163.com 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。
'''

INFO = r'''
锐派(rypi): 由锐白开发的派神(python)工具包，包含多种网络工具和实用程序模块。
锐网(ryweb): 网站服务器管理工具, 一个集成的 Web 服务器环境管理包，支持 Nginx、PostgreSQL、ArangoDB、SeaweedFS、Conda、Uvicorn、FastAPI、PHP 等组件。
锐鸥(ryo): 一款网站应用工具，包含服务端（发行商）、代理端（运营商），代理端为共享软件，由运营商（站长或平台运营者）使用，免费版只能使用基础功能，部分功能需要付费解锁。任何个人或企业都可以通过锐鸥(ryo)运营自己的内容平台，无需具备代码编程相关的知识，只需买一台服务器启动程序，选择开放相应的应用与工具供平台用户使用就可以坐享收益。
锐通(ryto): 通用/公用(Util)函数/工具库(Tools)。
锐代(rydy): 一款网络数据抓包代理工具。
锐辅(ryfu): 一款辅助工具, 可用于执行日常自动任务, 如: 游戏辅助, 广告辅助, 应用辅助。
锐爬(rypa): 一款网络内容爬取工具, 如新闻内容, 电影内容, 电商内容。
锐库(ryku): 一款简易数据库。
锐飞(ryben): 一款简易文件数据库。
锐窗(rywin): 图形窗口工具，方便在图形界面系统(PyQt)或终端(Urwid)进行图形可视化窗口创建。
锐爱(ryapp): 一款简易应用生成工具。

更多内容请前往 锐码 官网查阅: rymaa.cn
Pypi 源包仓库: https://pypi.org/project/rypi/
Gitee 源码仓库: https://gitee.com/rybby/rypi
作者: 锐白
主页: rybby.cn, ry.rymaa.cn
邮箱: rybby@163.com

使用流程
安装锐派(rypi): pip install rypi
安装依赖库: pip install requests fonttools pyotp
'''

HELP = r'''
+-------------------------------------------+
|        rypi: Rybby's Python Tools         |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -m, --module   Show module / 显示子模块
'''

##############################

import os
import sys
import argparse

# 脚本运行模式的路径修复
if __name__ == "__main__" and __package__ is None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    __package__ = 'rypi'

try: # 相对导入
    from . import conf
    from . import comm
except ImportError: # 包内导入
    from rypi import conf
    from rypi import comm

##############################

def main(args=None):
    '''
    入口主函数。
    返回: void
    参数列表：
        args (str): 参数列表，通过命令行传入或调用者传入。
    '''

    # 全局选项
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-H', '--help', action='store_true')
    parser.add_argument('-I', '--info', action='store_true')
    parser.add_argument('-C', '--copr', action='store_true')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-m', '--module', action='store_true')

    # 获取当前目录的所有子模块
    smod = comm._get_modules(__package__)

    # 创建子模块解析器
    subp = parser.add_subparsers(dest='smod', required=False)

    # 定义子模块
    for name, _, _ in smod:
        subp.add_parser(name, add_help=False)

    # 只解析到子模块名称，剩下的参数作为未知参数留给子模块处理
    args, args2 = parser.parse_known_args(args)
    #print(f'args: {args}, args2: {args2}')

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.help:
        print(HELP)

    # 显示子模块
    elif args.module:
        print(f'\n可以在模块名称后加参数(-H)查看该模块的帮助信息。')
        print(f'\n名称前面带横线(-)的是命令模块（目录），否则是辅助模块（脚本 .py 文件）。')
        print(f'\nmodule list:')
        for name, desc, ispkg in smod:
            sub = '-' if ispkg else ' '
            print(f'\n  {sub} {name}: {desc}')

    # 调用子模块
    elif args.smod:
        for name, desc, ispkg in smod:
            if name == args.smod:
                #print(f'name: {name}, args: {args2}')
                comm._run_mod(__package__, name, ispkg, args2)

    # 显示帮助
    else:
        print(HELP)

if __name__ == '__main__':
    main()