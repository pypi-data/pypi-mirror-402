#!/usr/bin/env python
'''
锐鸥(ryo)后端程序为共享软件，由运营商使用，免费版只能使用基础功能，部分功能需要付费解锁。
'''

VER = r'''
ryo version: 2026.1.15.0
'''

COPR = r'''
锐鸥(ryo)后端程序为共享软件，由运营商使用，禁止反编译、修改、分发、传播，免费版只能使用基础功能，部分功能需要付费解锁。
'''

INFO = r'''
锐鸥(ryo)后端程序为共享软件，由运营商使用，免费版只能使用基础功能，部分功能需要付费解锁。

服务端由发行商使用，用来处理代理端的用户数据。代理端的用户发布文章、商品等数据由代理端处理，用户数据（如：注册、登录、购买增值服务等）由代理端转发给服务端处理。

锐鸥(ryo)由扩展应用和扩展工具组成，代理端需要向服务端付费解锁相应的扩展应用和扩展工具，然后客户端才能使用这些应用和工具。

任何个人或企业都可以通过锐鸥(ryo)运营自己的内容平台，无需具备代码编程相关的知识，只需买一台服务器启动程序，选择开放相应的应用与工具供平台用户使用就可以坐享收益。
'''

HELP = r'''
+-------------------------------------------+
|              ryo: site tools              |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryo [option]

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
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root)
    __package__ = 'rypi.ryo'

try: # 相对导入
    from . import conf
    from .. import comm
except ImportError: # 包内导入
    from rypi.ryo import conf
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