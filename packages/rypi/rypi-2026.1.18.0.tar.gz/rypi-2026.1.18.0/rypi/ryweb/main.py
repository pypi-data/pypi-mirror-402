#!/usr/bin/env python
'''
锐网(ryweb) 是一款网站服务器管理工具(Website Server Management Tool), 一个集成的 Web 服务器管理包，支持 Nginx、PostgreSQL、ArangoDB、SeaweedFS、Conda、Uvicorn、FastAPI、PHP 等组件。
'''

VER = r'''
ryweb version: 2026.1.18.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] - rymaa_cn@163.com 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。
'''

INFO = r'''
锐网(ryweb) 是一款网站服务器管理工具(Website Server Management Tool), 一个集成的 Web 服务器管理包，支持 Nginx、PostgreSQL、ArangoDB、SeaweedFS、Conda、Uvicorn、FastAPI、PHP 等组件。

支持组件

Web服务器: Nginx
数据库: PostgreSQL, ArangoDB
文件存储: SeaweedFS
环境管理: Conda
应用服务器: Uvicorn, FastAPI
脚本支持: Python, PHP

使用流程

如果需要在网络上搭建网站服务器，在使用 锐网(ryweb) 前，请先获得一台服务器，推荐使用 [雨云](https://www.rainyun.com/OTMyMTQ2_)，这家服务商的云服务器很实惠。

如果数据盘未挂载，请使用命令 rypi ryto amdd 进行挂载，该命令会进行交互式操作并将挂载的数据盘设为开机自动挂载，通常将数据盘挂载为 /data。

挂载数据盘后就可以安装 锐派(rypi) 了:

pip install rypi

然后将 锐网(ryweb) 安装到数据盘了:

rypi ryweb install -p /data/ryweb

注意不要安装到系统盘，因为有时候需要重装系统或更换系统，那样的话会导致网站数据会全部丢失，所以一定要把 锐网(ryweb) 安装到非系统盘，默认的安装路径是 /var/www/ryweb，该路径是假设没有挂载数据盘时用的，如果你已经有数据盘了，请安装到数据盘，如: /data/ryweb，安装程序会自动创建下列目录：

/data/ryweb/app # 安装需要下载的服务应用保存在这里

/data/ryweb/web # 存放网站的静态文件，如果安装多台主机请用一级域名作为网站的根目录，如：rymaa.cn

/data/ryweb/cfg # nginx 的配置文件目录为：cfg/nginx，各主机的配置文件在该目录的子目录 cfg/nginx/vhost 下

/data/ryweb/db # 数据库存放目录

/data/ryweb/env # 虚拟环境存放目录

/data/ryweb/code # 后端程序存放目录，各主机以网站域名作为目录，如果服务器使用 nginx+fastapi 模式，安装程序会默认使用锐鸥(ryo) 作为网站的后端应用程序，若网站运营者想用其它的后端网站应用，可在 code 目录的主机目录添加 app.py，并在 app.py 内设置 api 函数作为应用入口，api 函数根据客户端提交的接口名执行相应的程序并返回数据（数据格式为 cpo 或 json）给客户端，接口键名为 f，被调用的接口函数必须在白名单列表中。

后端应用程序导入的优先顺序：app.py > rypi.ryo 或 app.php > ryo.php

锐鸥(ryo)是一款网站应用工具，包含服务端（发行商）、代理端（运营商），代理端为共享软件，由运营商（站长或平台运营者）使用，免费版只能使用基础功能，部分功能需要付费解锁。任何个人或企业都可以通过锐鸥(ryo)运营自己的内容平台，无需具备代码编程相关的知识，只需买一台服务器启动程序，选择开放相应的应用与工具供平台用户使用就可以坐享收益。

在 锐网(ryweb) 安装 FastAPI 时会自动安装这些依赖包: FastAPI, Uvicorn, python-multipart, rypi，如果需要更新请用命令 rypi ryweb pkg -n/name(包名) [-u/update(升级安装), -o/origin(指定仓库源，如果值为 1 则使用 pypi 的官方仓库源)] 进行安装或更新。如果要安装开发包请将 包名 设为 .项目包路径，如：rypi ryweb pkg -n ./data/pjt_rypi，开发包方便开发时修改源码进行调式。

注意！这些依赖包是安装到虚拟环境 ryweb，与系统安装的依赖包不冲突，如果你的后端程序是用 python 开发且用到其它库，必须将这些库安装到虚拟环境 ryweb，因为 锐网(ryweb) 是在虚拟环境中运行的。

关于运行模式

运行模式是指服务器环境要运行哪些服务，常见的组合如下：

np = nginx + php
npp = nginx + php + postgresql
nf = nginx + fastapi
nfp = nginx + postgresql + fastapi
nfpc = nginx + postgresql + conda + fastapi
nfas = nginx + arangodb + seaweedfs + fastapi
nfasc = nginx + arangodb + seaweedfs + conda + fastapi

安装服务器时如不指定运行模式则使用默认的 nfp，后期如果想更换可用 mode 命令，如：
rypi ryweb mode npp

目前锐网(ryweb)安装时会自动将锐鸥(ryo)作为后端程序，如果想用其它后端程序请在代码目录的主机目录(如code/rymaa.cn/)放置自己的后端程序，如：app.py 或 app.php，app 程序里必须有一个 api 函数作为入口，出于安全考虑，请将所有可通过前端调用的接口函数加入函数白名单。

目前锐网(ryweb)的运行模式 nfp 可正常运行，其它模式正在调试中，还有锐鸥目前仅推出 python 版本，因为 python 可以方便调用很多开源库，如 AI项目、训练模型等，php 则没有这么方便。

更多内容请前往 锐码 官网查阅: rymaa.cn
作者: 锐白
主页: rybby.cn, ry.rymaa.cn
邮箱: rybby@163.com
'''

HELP = r'''
+-------------------------------------------+
|   ryweb: Website Server Management Tool   |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi ryweb [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    
    install -p/--path 管理器路径 -m/--mode 运行模式 # 安装网站环境管理器，默认路径：/var/www/ryweb
    start # 启动网站所有服务(不同的运行模式有不同的服务)
    stop # 停止网站所有服务(不同的运行模式有不同的服务)
    reload # 重启网站所有服务(不同的运行模式有不同的服务)
    start ngi # 启动恩金克斯(Nginx)
    stop ngi # 停止恩金克斯(Nginx)
    reload ngi # 重启恩金克斯(Nginx)
    start psql # 启动 PostgreSQL
    stop psql # 停止 PostgreSQL
    reload psql # 重启 PostgreSQL
    start adb # 启动浪哥/橙子(ArangoDB)
    stop adb # 停止浪哥/橙子(ArangoDB)
    reload adb # 重启浪哥/橙子(ArangoDB)
    start sfs # 启动海草(SeaWeedFS)
    stop sfs # 停止海草(SeaWeedFS)
    reload sfs # 重启海草(SeaWeedFS)
    start uvi # 启动优维康(Uvicorn)
    stop uvi # 停止优维康(Uvicorn)
    reload uvi # 重启优维康(Uvicorn)
    start php # 启动 PHP
    stop php # 停止 PHP
    reload php # 重启 PHP
    mode 模式类型，如：npp # 修改运行模式
    app 服务应用，如：nginx，php -i/isnew(是否全新安装，0=否，1=是) # 安装服务应用
    pkg -n/name(包名，如需指定版本请用：pkgname==ver，如果要将一个代码路径安装为开发包，请用点号加路径，如 rypi ryweb pkg -n './data/pjt_rypi') -u/update(升级安装) -o/origin(指定仓库源，如果值为 1 则使用 pypi 的官方仓库源) # 安装依赖包
    unpkg -n/name(包名) # 卸载依赖包
    add -n/--name(主机名(目录名)，通常以域名作为主机名，如：rymaa.cn) -d/--dmlist(域名列表，如：abc.com www.abc.com *.abc.com) # 添加主机
    del -n/--name(主机名(目录名)) # 删除主机
    ssl -n/--name(主机名(目录名)) -d/--dmlist(域名列表，如果不需要泛域名则设为：abc.com www.abc.com，如果要泛域名则不能加 www 这个二级域名，正确的是：abc.com *.abc.com) -e/--email(申请 SSL 的邮箱，留空则使用默认的 ryweb@rymaa.cn) # 为主机设置 SSL
    ssldel -n/--name(主机名(目录名)，通常以域名作为主机名，如：rymaa.cn) # 删除指定主机的 SSL 证书
    pass -t/--type(修改指定类型的密码：user=修改admin的密码，psql=PostgreSQL，adb=ArangoDB，sfs=SeaWeedFS) -p/--pass(密码) # 设置密码
'''

##############################

import os
import sys
import argparse
import subprocess
import re
import requests
import json
import time
import shutil
import platform
import tarfile
import zipfile
import urllib.request
from pathlib import Path
from typing import List
import socket
import select
import logging
logger = logging.getLogger(__name__)

# 脚本运行模式的路径修复
if __name__ == "__main__" and __package__ is None:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root)
    __package__ = 'rypi.ryweb'

try: # 相对导入
    from .conf import *
    from .. import comm
except ImportError: # 包内导入
    from rypi.ryweb.conf import *
    from rypi import comm

##############################

class RyWeb:
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.is_linux = self.system == 'linux'
        self.is_windows = self.system == 'windows'
        self.is_mac = self.system == 'darwin'
        self.appmap = {
            'ngi': 'nginx',
            'psql': 'postgres',
            'adb': 'arangodb',
            'sfs': 'seaweedfs',
            'con': 'conda',
            'fas': 'fastapi',
            'php': 'php',
            'cer': 'certbot',
            'env': 'env'
        }
        
    def chsv(self):
        """改变服务名称映射"""
        if run_mode == 'nfas' or run_mode == 'nfasc':
            self.service_map = {
                'ngi': 'nginx',
                'adb': 'arangodb',
                'sfs': 'seaweedfs',
                'uvi': 'uvicorn'
            }
        elif run_mode == 'nfp' or run_mode == 'nfpc':
            self.service_map = {
                'ngi': 'nginx',
                'psql': 'postgres',
                'uvi': 'uvicorn'
            }
        elif run_mode == 'np':
            self.service_map = {
                'ngi': 'nginx',
                'php': 'php-fpm'
            }
        elif run_mode == 'nf':
            self.service_map = {
                'ngi': 'nginx',
                'uvi': 'uvicorn'
            }
        else:
            self.service_map = {
                'ngi': 'nginx',
                'psql': 'postgres',
                'php': 'php-fpm'
            }

    def mkdir(self):
        """创建目录"""
        global www_root, app_dir, web_dir, cfg_dir, db_dir, psql_dir, adb_dir, sfs_dir, ssl_dir, env_dir, code_dir, nginx_cfg_dir, nginx_host_dir, nginx_logs_dir, nginx_body_dir, nginx_proxy_dir, nginx_fastcgi_dir, nginx_uwsgi_dir, nginx_scgi_dir, adb_logs_dir, adb_data_dir, adb_apps_dir
        
        app_dir = lpath(www_root, 'app')
        web_dir = lpath(www_root, 'web')
        cfg_dir = lpath(www_root, 'cfg')
        db_dir = lpath(www_root, 'db')
        psql_dir = lpath(db_dir, 'psql')
        adb_dir = lpath(db_dir, 'adb')
        sfs_dir = lpath(db_dir, 'sfs')
        ssl_dir = lpath(www_root, 'ssl')
        env_dir = lpath(www_root, 'env')
        code_dir = lpath(www_root, 'code')
        nginx_cfg_dir = lpath(cfg_dir, 'nginx')
        nginx_host_dir = lpath(cfg_dir, 'nginx', 'vhost')
        nginx_logs_dir = lpath(cfg_dir, 'nginx', 'logs')
        nginx_body_dir = lpath(cfg_dir, 'nginx', 'temp', 'client_body_temp')
        nginx_proxy_dir = lpath(cfg_dir, 'nginx', 'temp', 'proxy_temp')
        nginx_fastcgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'fastcgi_temp')
        nginx_uwsgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'uwsgi_temp')
        nginx_scgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'scgi_temp')
        adb_logs_dir = lpath(adb_dir, 'adb', 'logs')
        adb_data_dir = lpath(adb_dir, 'adb', 'data')
        adb_apps_dir = lpath(adb_dir, 'adb', 'apps')

        dirs = [www_root, app_dir, web_dir, cfg_dir, db_dir, psql_dir, adb_dir, sfs_dir, ssl_dir, env_dir, code_dir, nginx_cfg_dir, nginx_host_dir, nginx_logs_dir, nginx_body_dir, nginx_proxy_dir, nginx_fastcgi_dir, nginx_uwsgi_dir, nginx_scgi_dir, adb_logs_dir, adb_data_dir, adb_apps_dir]

        for dir in dirs:
            os.makedirs(dir, exist_ok=True)

        self.run_cmd(f'sudo chmod -R 755 {nginx_cfg_dir}')
        self.run_cmd(f'sudo chown -R {www_user}:{www_user} {web_dir}')
        self.run_cmd(f'sudo chmod -R 755 {web_dir}')
        self.run_cmd(f'sudo chmod -R 755 {env_dir}')
        self.run_cmd(f'sudo chown -R arangodb:arangodb {adb_dir}')
        self.run_cmd(f'sudo chmod -R 755 {adb_dir}')
    
    def lpath(self, *dirs):
        """将 dirs 中的文件名连接成路径"""
        path = os.path.join(*dirs)
        path = os.path.expandvars(path) # 展开环境变量 %APPDATA%
        path = os.path.expanduser(path) # 展开 ~
        path = os.path.abspath(path).replace('\\', '/')
        return path

    def restr(self, str, **kvs):
        """将 str 中的关键词用 kvs 里的值进行替换，不存在的key替换为空串"""
        pattern = r'<<(\w+)>>'
        return re.sub(pattern, lambda m: kvs.get(m.group(1), ''), str)

    def newfile(self, path, ctt):
        """创建新文件"""
        if isinstance(path, list):
            path = self.lpath(*path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(ctt)
    
    def set_env_var(self, key: str, value: str) -> bool:
        """
        永久设置用户级环境变量（重启终端/登录后生效），**覆盖已有值**。
        支持 Windows、Linux、macOS。

        参数:
            key (str): 环境变量名，如 'WEB_ROOT'
            value (str): 环境变量值，如 '/var/www/webroot'

        返回:
            bool: 成功返回 True，否则 False。
        """

        if not isinstance(key, str) or not isinstance(value, str):
            print("Key and value must be strings.", file=sys.stderr)
            return False

        if not key or '=' in key or ' ' in key or not key.isidentifier():
            print(f"Invalid environment variable name: {key}", file=sys.stderr)
            return False

        try:
            if self.is_windows:
                return self._set_env_var_win(key, value)
            elif self.is_linux or self.is_mac:
                return self._set_env_var_unix(key, value)
            else:
                raise OSError(f"Unsupported OS: {self.system}")
        except Exception as e:
            print(f"Error setting environment variable permanently: {e}", file=sys.stderr)
            return False

    def _set_env_var_win(self, key: str, value: str) -> bool:
        """Windows: 通过注册表设置（自动覆盖）"""

        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            ) as reg_key:
                winreg.SetValueEx(reg_key, key, 0, winreg.REG_SZ, value)

            # 通知系统
            try:
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
            except Exception:
                pass

            os.environ[key] = value
            return True
        except Exception as e:
            print(f"Failed to set environment variable on Windows: {e}", file=sys.stderr)
            return False

    def _set_env_var_unix(self, key: str, value: str) -> bool:
        """Linux/macOS: 覆盖式写入 shell 配置文件"""
        home = os.path.expanduser("~")
        shells_config: List[str] = []

        if self.is_mac:
            shells_config = [
                os.path.join(home, ".zshrc"),
                os.path.join(home, ".bash_profile"),
                os.path.join(home, ".bashrc")
            ]
        else:  # Linux
            shells_config = [
                os.path.join(home, ".bashrc"),
                os.path.join(home, ".profile"),
                os.path.join(home, ".zshrc")
            ]

        # 根据当前 SHELL 优先处理
        default_shell = os.environ.get('SHELL', '')
        if 'zsh' in default_shell:
            primary = os.path.join(home, ".zshrc")
            if primary not in shells_config:
                shells_config.insert(0, primary)
        elif 'bash' in default_shell:
            primary = os.path.join(home, ".bashrc")
            if primary not in shells_config:
                shells_config.insert(0, primary)

        # 转义双引号
        safe_value = value.replace('"', '\\"')
        new_line = f'export {key}="{safe_value}"\n'
        marker_comment = "# Added or updated by ryweb"

        # 优先修改第一个存在的配置文件
        target_file = None
        for config in shells_config:
            if os.path.isfile(config):
                target_file = config
                break

        # 如果都不存在，回退到 .bashrc
        if target_file is None:
            target_file = os.path.join(home, ".bashrc")

        try:
            # 读取现有内容（若文件存在）
            if os.path.isfile(target_file):
                with open(target_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []

            # 过滤掉所有与 key 相关的 export 或赋值行（支持多种格式）
            filtered_lines = []
            key_pattern = re.compile(rf'^\s*(export\s+)?{re.escape(key)}\s*=')

            for line in lines:
                if key_pattern.match(line) or marker_comment in line:
                    continue  # 跳过旧的定义和标记行
                filtered_lines.append(line)

            # 确保末尾有换行
            if filtered_lines and not filtered_lines[-1].endswith('\n'):
                filtered_lines[-1] += '\n'

            # 添加新定义（带标记注释便于识别）
            filtered_lines.append(f'\n{marker_comment}\n{new_line}')

            # 写回文件
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)

            os.environ[key] = value
            return True

        except (OSError, IOError) as e:
            print(f"Failed to write to config file {target_file}: {e}", file=sys.stderr)
            return False
        
    def get_env_var(self, key: str, default=None):
        """
        获取环境变量的当前值。
        
        行为：
          - 首先从当前进程环境 (os.environ) 中获取（最常用、最可靠）
          - 若未找到 且 在 Windows 上，则尝试从用户注册表中读取（即使未生效）
          - 在 Linux/macOS 上，不解析 shell 配置文件（因复杂且易错）

        参数:
            key (str): 环境变量名
            default: 默认值（若未找到）

        返回:
            str 或 default
        """
        # 1. 先查当前进程环境（所有平台通用）
        value = os.environ.get(key)
        if value is not None:
            return value

        # 2. Windows：回退到读取注册表（用户级）
        if self.is_windows:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key_reg:
                    val, _ = winreg.QueryValueEx(key_reg, key)
                    return val
            except (ImportError, FileNotFoundError, OSError):
                pass  # 注册表中也不存在

        # 3. Unix: 不主动解析 .bashrc 等（避免复杂性）
        #    用户应确保变量已 source 或在新终端中生效

        return default

    def set_env_var_file(self, key='', value=''):
        """设置环境变量到文件"""
        if self.is_windows:
            dir = self.lpath('%APPDATA%', 'ryweb')
        else:
            dir = self.lpath('~', '.config', 'ryweb')
        os.makedirs(dir, exist_ok=True)
        path = self.lpath(dir, 'env_var.json')

        env_var = {}
        if os.path.exists(path):
            with open(path, 'r') as f:
                env_var = json.load(f)
        env_var[key] = value

        with open(path, 'w') as f:
            json.dump(env_var, f)

        return dir

    def get_env_var_file(self, key=''):
        """从文件获取环境变量"""
        if self.is_windows:
            dir = self.lpath('%APPDATA%', 'ryweb')
        else:
            dir = self.lpath('~', '.config', 'ryweb')
        os.makedirs(dir, exist_ok=True)
        path = self.lpath(dir, 'env_var.json')

        if not os.path.exists(path):
            return None

        with open(path, 'r') as f:
            env_var = json.load(f)

        for k, v in env_var.items():
            if k == key:
                return v
        return None

    def add_path(self, path: str) -> bool:
        """
        将指定路径添加到当前进程的 PATH 环境变量中。
        
        参数:
            path (str): 要添加的路径（应为绝对路径）。
            
        返回:
            bool: 如果成功添加返回 True，否则返回 False。
        """
        if not os.path.isdir(path):
            # 可选：如果路径不存在，可以选择抛出异常或静默失败
            return False

        # 规范化路径（处理斜杠等）
        path = os.path.abspath(path)

        # 获取当前 PATH
        current_path = os.environ.get('PATH', '')
        path_list = current_path.split(os.pathsep)

        # 避免重复添加
        if path in path_list:
            return True  # 已存在，视为成功

        # 添加到 PATH 开头（也可以加到末尾，根据需求调整）
        path_list.insert(0, path)
        os.environ['PATH'] = os.pathsep.join(path_list)

        return True
    
    def add_path_to_env(self, path: str) -> bool:
        """
        永久将路径添加到当前用户的 PATH 环境变量中（重启终端生效）。
        支持 Windows、Linux、macOS。
        
        参数:
            path (str): 要添加的绝对路径。
            
        返回:
            bool: 成功返回 True，否则 False。
        """
        if not os.path.isdir(path):
            return False

        path = os.path.abspath(path)

        try:
            if self.is_windows:
                return self._add_path_win(path)
            elif self.is_linux or self.is_mac:
                return self._add_path_unix(path)
            else:
                raise OSError(f"Unsupported OS: {self.system}")
        except Exception as e:
            print(f"Error adding path permanently: {e}", file=sys.stderr)
            return False

    def _add_path_win(self, path: str) -> bool:
        """Windows: 使用 PowerShell 修改当前用户的 PATH"""

        try:
            import winreg
            # 打开当前用户的环境变量注册表项
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Environment",
                                0, winreg.KEY_READ | winreg.KEY_WRITE) as key:

                current_path, _ = winreg.QueryValueEx(key, "PATH")
                path_list = current_path.split(";") if current_path else []

                # 去重
                if path in path_list:
                    return True

                # 添加到末尾
                new_path = ";".join(path_list + [path])
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)

            # 可选：通知系统环境变量已更改（使资源管理器等感知）
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")

            return True
        except Exception as e:
            print(f"Windows PATH update failed: {e}", file=sys.stderr)
            return False

    def _add_path_unix(self, path: str) -> bool:
        """Linux/macOS: 修改 shell 配置文件（~/.bashrc, ~/.zshrc 等）"""
        home = os.path.expanduser("~")
        shells_config = []

        # 根据常用 shell 列出可能的配置文件
        if self.is_mac:
            # macOS 默认使用 zsh
            shells_config = [
                os.path.join(home, ".zshrc"),
                os.path.join(home, ".bash_profile"),
                os.path.join(home, ".bashrc")
            ]
        else:  # Linux
            shells_config = [
                os.path.join(home, ".bashrc"),
                os.path.join(home, ".profile"),
                os.path.join(home, ".zshrc")
            ]

        # 获取当前默认 shell（用于优先处理）
        default_shell = os.environ.get('SHELL', '')
        if 'zsh' in default_shell:
            primary = os.path.join(home, ".zshrc")
            if primary not in shells_config:
                shells_config.insert(0, primary)
        elif 'bash' in default_shell:
            primary = os.path.join(home, ".bashrc")
            if primary not in shells_config:
                shells_config.insert(0, primary)

        line_to_add = f'\n# Added by ryweb\nexport PATH="{path}:$PATH"\n'

        modified = False
        for config_file in shells_config:
            if not os.path.exists(config_file):
                continue

            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已存在该路径（简单匹配）
            if path in content:
                continue  # 已存在，跳过

            # 追加
            with open(config_file, 'a', encoding='utf-8') as f:
                f.write(line_to_add)
            modified = True
            break  # 只修改一个主要配置文件即可

        # 如果没有找到任何配置文件，创建 .bashrc（保守策略）
        if not modified:
            fallback = os.path.join(home, ".bashrc")
            with open(fallback, 'a', encoding='utf-8') as f:
                f.write(line_to_add)
            modified = True

        return modified
    
    def download_file(self, url, filename):
        """下载文件"""
        def progress_hook(block_num, block_size, total_size):
            """
            进度回调函数
            - block_num: 当前已下载的块数量
            - block_size: 每个块的大小（字节）
            - total_size: 文件总大小（字节），如果未知则为0
            """
            downloaded = block_num * block_size
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\r下载进度: {percent:.1f}% ({downloaded:,} / {total_size:,} bytes)", end='', flush=True)
            else:
                print(f"\r已下载: {downloaded:,} bytes", end='', flush=True)

        filepath = self.lpath(app_dir, filename)
        
        print(f"\n准备下载: {url}")
        
        if os.path.exists(filepath):
            print(f"\n文件已存在: {filename}")
            return filepath
        
        try:
            print(f"\n下载中...")
            urllib.request.urlretrieve(url, filepath, progress_hook)
            print(f"\n下载完成: {filename}")
            return filepath
        except Exception as e:
            print(f"\n下载失败: {e}")
            return None
    
    def extract_file(self, filepath, extract_to):
        """解压文件"""
        print(f"\n解压: {os.path.basename(filepath)} -> {extract_to}")
        
        if filepath.endswith('.tar.gz') or filepath.endswith('.tgz'):
            with tarfile.open(filepath, 'r:gz') as tar:
                tar.extractall(extract_to)
        elif filepath.endswith('.zip'):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        else:
            print(f"\n不支持的文件格式: {filepath}")
            return False
        return True
    
    def find_extracted_dir(self, base_dir, pattern):
        """在基础目录中搜索匹配模式的解压目录"""
        if not os.path.exists(base_dir):
            return None
        
        for item in os.listdir(base_dir):
            item_path = self.lpath(base_dir, item)
            if os.path.isdir(item_path) and pattern in item:
                return item_path
        
        return None

    def run_cmd(self, cmd, shell=True, check=False, capout=True, tmout=30, back=True):
        """运行命令"""
        try:
            if capout == 'null':
                stdout = subprocess.DEVNULL
                stderr = subprocess.DEVNULL
            elif capout == 'eo':
                stdout = subprocess.PIPE
                stderr = subprocess.STDOUT
            elif capout == False:
                stdout = None
                stderr = None
            else:
                stdout = subprocess.PIPE
                stderr = subprocess.PIPE
            if shell:
                if back == False:
                    cmd = f'{cmd} -g "daemon off;"'
                res = subprocess.run(cmd, shell=True, text=True, check=check, timeout=tmout, stdout=stdout, stderr=stderr)
            else:
                if back == False:
                    cmd = [cmd, '-g', '"daemon off;"']
                res = subprocess.run(cmd, shell=False, text=True, check=check, timeout=tmout, stdout=stdout, stderr=stderr)
            return res
        except subprocess.CalledProcessError as e:
            print(f"\n命令执行失败: {e}")
            if e.stderr:
                print(f"\n错误输出: {e.stderr}")
            return e
    
    def open_cmd(self, cmd, shell=True, capout=True, back=True, res=False):
        """运行命令"""
        if capout == 'null':
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        elif capout == 'eo' or res == 'poll':
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT
        elif capout == True:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            stdout = None
            stderr = None

        if shell:
            if back == False:
                cmd = f'{cmd} -g "daemon off;"'
            proc = subprocess.Popen(cmd, shell=True, text=True, stdout=stdout, stderr=stderr)
        else:
            if back == False:
                cmd = [cmd, '-g', '"daemon off;"']
            proc = subprocess.Popen(cmd, shell=False, text=True, stdout=stdout, stderr=stderr)

        if res == 'code':
            code = proc.wait()
            return {'code':code, 'out':None, 'err':None}
        
        elif res == 'out':
            out, err = proc.communicate()
            code = proc.returncode
            return {'code':code, 'out':out, 'err':err}
        
        elif res == 'poll':
            out = []
            while True:
                # 读取一个字符
                char = proc.stdout.read(1)
                if char:
                    # 立即打印到屏幕并保存到输出
                    print(char, end='', flush=True)
                    out.append(char)
                else:
                    # 没有字符可读，检查进程是否结束
                    if proc.poll() is not None:
                        break
            
            # 最后换行并返回完整输出
            print()
            out = ''.join(out)
            return {'code':proc.returncode, 'out':out, 'err':None}
        
        return proc
    
    def install_nginx(self, new='0'):
        """安装 Nginx"""
        
        print("\n准备安装 Nginx")

        if shutil.which('nginx') and new=='0':
            res = self.run_cmd('nginx -v', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split('/')[1].strip()
            print(f'\n已存在 Nginx, 当前版本: {ver}')
            global nginx_ver
            nginx_ver = ver
            return
        
        if self.is_linux:
            if shutil.which('apt'):
                print("\n使用 apt 安装 Nginx...")
                res = self.open_cmd("sudo apt install -y nginx", capout=False, res='out')
            elif shutil.which('yum'):
                print("\n使用 yum 安装 Nginx...")
                res = self.open_cmd("sudo yum install -y nginx", capout=False, res='out')
            elif shutil.which('dnf'):
                print("\n使用 dnf 安装 Nginx...")
                res = self.open_cmd("sudo dnf install -y nginx", capout=False, res='out')
            else:
                print("\n无法找到支持的包管理器，跳过 Nginx 安装")
                return False
            
            if res['code'] != 0:
                print(f"\n❌ Nginx 安装失败:\n{res['err']}")
                return False
            
        elif self.is_windows:
            pkg_url = nginx_pkg_win
            filename = os.path.basename(pkg_url)
            filepath = self.download_file(pkg_url, filename)
            if not filepath:
                return False

            print(f"\n正在安装 Nginx...")
            if self.extract_file(filepath, app_dir):
                app_dir_nginx = self.find_extracted_dir(app_dir, f"nginx-{nginx_ver}")
                if not app_dir_nginx:
                    app_dir_nginx = self.find_extracted_dir(app_dir, "nginx")
                # 将nginx目录添加到系统环境变量与环境路径
                if app_dir_nginx:
                    self.set_env_var_file('RYWEB_NGINX_ROOT', app_dir_nginx)
                    self.add_path_to_env(app_dir_nginx)
                    #print(f'path: {os.environ.get("PATH", "")}')
                    
        elif self.is_mac:
            res = self.open_cmd('brew install nginx', capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ Nginx 安装失败")
                return False
        else:
            print("未知系统，跳过 Nginx 安装")
            return False

        # 设置网站用户
        self.add_www_user()

        # 创建 mime 类型文件
        self.newfile([nginx_cfg_dir, 'mime.types'], mime_types)

        # 创建配置文件
        nouser = '#'
        if self.is_linux:
            nouser = ''
        ctt = self.restr(nginx_conf, nouser=nouser, www_user=www_user, web_dir=web_dir, nginx_logs_dir=nginx_logs_dir, nginx_body_dir=nginx_body_dir, nginx_proxy_dir=nginx_proxy_dir, nginx_fastcgi_dir=nginx_fastcgi_dir, nginx_uwsgi_dir=nginx_uwsgi_dir, nginx_scgi_dir=nginx_scgi_dir)
        self.newfile([nginx_cfg_dir, 'nginx.conf'], ctt)
        
        # 创建路由器脚本文件
        self.newfile([code_dir, 'router.php'], router_ctt)
        
        print("\n✅ 成功安装 Nginx")
        return True
    
    def add_www_user(self):
        """添加网站用户"""
        if self.is_linux:
            print(f"\n添加网站用户: {www_user}")
            
            # 检查用户是否存在
            result = self.run_cmd(f"id {www_user}")
            if result.returncode != 0:
                # 创建用户和组
                self.run_cmd(f"sudo groupadd {www_user}")
                self.run_cmd(f"sudo useradd -r -g {www_user} -s /bin/false {www_user}")
                print(f"\n✅ 创建用户: {www_user}")
            else:
                print(f"\n✅ 用户已存在: {www_user}")
            
            # 设置目录权限
            self.run_cmd(f"sudo chown -R {www_user}:{www_user} {web_dir}")
            self.run_cmd(f"sudo chmod -R 755 {web_dir}")
            
        elif self.is_windows:
            print("\nWindows 平台跳过用户设置")
            return True
        
        return True

    def install_postgresql(self, new='0'):
        """安装 PostgreSQL"""
        
        print("\n准备安装 PostgreSQL")

        if shutil.which('psql') and new=='0':
            res = self.run_cmd('psql -V', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split(' ')[2].strip()
            print(f'\n已存在 PostgreSQL, 当前版本: {ver}')
            global postgresql_ver
            postgresql_ver = ver
            return
        
        if self.is_linux:
            if shutil.which('apt'):
                print("\n使用 apt 安装 PostgreSQL...")
                res = self.open_cmd("sudo apt install -y postgresql", capout=False, res='out')
            elif shutil.which('yum'):
                print("\n使用 yum 安装 PostgreSQL...")
                res = self.open_cmd("sudo yum install -y postgresql-server", capout=False, res='out')
            elif shutil.which('dnf'):
                print("\n使用 dnf 安装 PostgreSQL...")
                res = self.open_cmd("sudo dnf install -y postgresql-server", capout=False, res='out')
            else:
                print("\n无法找到支持的包管理器，跳过 PostgreSQL 安装")
                return False
            
            if res['code'] != 0:
                print(f"\n❌ PostgreSQL 安装失败")
                return False
            
        elif self.is_windows:
            pkg_url = postgresql_win
            filename = os.path.basename(pkg_url)
            filepath = self.download_file(pkg_url, filename)
            if not filepath:
                return False

            print(f"\n正在安装 PostgreSQL...")
            if self.extract_file(filepath, app_dir):
                app_dir_postgresql = self.find_extracted_dir(app_dir, f"postgresql-{postgresql_ver}")
                if not app_dir_postgresql:
                    app_dir_postgresql = self.find_extracted_dir(app_dir, "pgsql")
                app_dir_postgresql = self.lpath(app_dir_postgresql, "bin")
                # 将 PostgreSQL 目录添加到系统环境变量与环境路径
                if app_dir_postgresql:
                    self.set_env_var_file('RYWEB_POSTGRESQL_ROOT', app_dir_postgresql)
                    self.add_path_to_env(app_dir_postgresql)
                    #print(f'path: {os.environ.get("PATH", "")}')
                    
        elif self.is_mac:
            res = self.open_cmd('brew install postgresql', capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ PostgreSQL 安装失败")
                return False
        else:
            print("未知系统，跳过 PostgreSQL 安装")
            return False

        print("\n✅ 成功安装 PostgreSQL")
        return True
    
    def install_arangodb(self, new='0'):
        """安装 ArangoDB"""
        
        print("\n准备安装 ArangoDB")

        if shutil.which('arangod') and new=='0':
            res = self.run_cmd('arangod --version', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split('\n')[0].strip()
            print(f'\n已存在 ArangoDB, 当前版本: {ver}')
            global arangodb_ver
            arangodb_ver = ver
            return
        
        if self.is_linux:
            if shutil.which('apt'):
                pkg_url = arangodb_pkg_deb
            elif shutil.which('yum') or shutil.which('dnf'):
                pkg_url = arangodb_pkg_rpm
            else:
                pkg_url = arangodb_pkg_lin
        elif self.is_windows:
            pkg_url = arangodb_pkg_win
        elif self.is_mac:
            pkg_url = arangodb_pkg_mac
        else:
            pkg_url = arangodb_pkg_lin
        
        filename = os.path.basename(pkg_url)
        filepath = self.download_file(pkg_url, filename)
        
        if not filepath:
            return False

        print("\n正在安装 ArangoDB...")
        if filename.endswith('.deb'):
            res = self.open_cmd(f"sudo dpkg -i {filepath}", capout=False, res='out')
        elif filename.endswith('.rpm'):
            res = self.open_cmd(f"sudo rpm -i {filepath}", capout=False, res='out')
        elif filename.endswith('.exe'):
            res = self.open_cmd(f"start /wait {filepath}", capout=False, res='out')
        elif filename.endswith('.dmg'):
            res = self.open_cmd(f"hdiutil attach {filepath} && sudo cp -R /Volumes/ArangoDB3-{arangodb_ver} /Applications/", capout=False, res='out')
        else:
            print('未知文件类型')
            
        if res['code'] != 0:
            print(f"\n❌ ArangoDB 安装失败")
            return False
        
        print("\n✅ 成功安装 ArangoDB")
        return True
    
    def install_seaweedfs(self, new='0'):
        """安装 SeaweedFS"""
        
        print("\n准备安装 SeaweedFS")
        
        if shutil.which('weed') and new=='0':
            res = self.run_cmd('weed version', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split(' ')[2].strip()
            print(f'\n已存在 SeaweedFS, 当前版本: {ver}')
            global seaweedfs_ver
            seaweedfs_ver = ver
            return
        
        if self.is_linux:
            pkg_url = seaweedfs_pkg_lin
        elif self.is_windows:
            pkg_url = seaweedfs_pkg_win
        elif self.is_mac:
            pkg_url = seaweedfs_pkg_mac
        else:
            pkg_url = seaweedfs_pkg_lin
        
        filename = os.path.basename(pkg_url)
        filepath = self.download_file(pkg_url, filename)
        
        if not filepath:
            return False

        print("\n正在安装 SeaweedFS...")
        if self.extract_file(filepath, app_dir):
            if self.is_windows:
                app_dir_weed = self.find_extracted_dir(app_dir, f"weed-{seaweedfs_ver}")
                if not app_dir_weed:
                    app_dir_weed = self.find_extracted_dir(app_dir, "weed")
                # 将 weed 复制到系统路径
                if app_dir_weed:
                    weed = self.lpath(app_dir_weed, "weed.exe")
                    if os.path.isfile(weed):
                        sys_dir = os.environ.get('SYSTEMROOT', 'C:/Windows')
                        shutil.copy(weed, sys_dir)
                        print(f'复制 {weed} 到 {sys_dir}')
            else:
                app_dir_weed = self.find_extracted_dir(app_dir, f"weed-{seaweedfs_ver}")
                if not app_dir_weed:
                    app_dir_weed = self.find_extracted_dir(app_dir, "weed")
                # 将 weed 复制到系统路径
                if app_dir_weed:
                    weed = self.lpath(app_dir_weed, "weed")
                    if os.path.isfile(weed):
                        sys_bin = '/usr/local/bin/weed'
                        self.run_cmd(f"sudo cp {weed} {sys_bin}")
                        self.run_cmd(f"sudo chmod +x {sys_bin}")
                        print(f'复制 {weed} 到 {sys_bin}')

        print("\n✅ 成功安装 SeaweedFS")
        return True
    
    def install_conda(self, new='0'):
        """安装 Conda"""
        
        print("\n准备安装 Conda")
        
        if shutil.which('conda') and new=='0':
            res = self.run_cmd('conda --version', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split(' ')[1].strip()
            print(f'\n已存在 Conda, 当前版本: {ver}')
            global conda_ver
            conda_ver = ver
            return
        
        if self.is_linux:
            pkg_url = conda_pkg_lin
        elif self.is_windows:
            pkg_url = conda_pkg_win
        elif self.is_mac:
            pkg_url = conda_pkg_mac
        else:
            pkg_url = conda_pkg_lin
        
        filename = os.path.basename(pkg_url)
        filepath = self.download_file(pkg_url, filename)
        
        if not filepath:
            return False
        
        # 清理可能存在的旧安装
        conda_dir = self.lpath(app_dir, 'miniconda3')
        if os.path.exists(conda_dir):
            print("\n清理旧的 Conda 安装...")
            try:
                shutil.rmtree(conda_dir)
            except Exception as e:
                print(f"清理失败: {e}")
    
        print("\n正在安装 Conda...")
        if filename.endswith('.sh'):
            res = self.open_cmd(f"bash {filepath} -b -p {conda_dir}", capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ Conda 安装失败")
                return False
            conda_bin = self.lpath(conda_dir, 'bin', 'conda')
            self.run_cmd(f"sudo ln -sf {conda_bin} /usr/local/bin/conda")

        elif filename.endswith('.exe'):
            res = self.open_cmd(f"start /wait {filepath}", capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ Conda 安装失败")
                return False
        
        print("\n初始化 Conda...")
        res = self.run_cmd("conda init bash")
        if res.returncode != 0:
            print("\n❌ Conda 初始化失败")
            return False
        print("\n✅ Conda 初始化完成")
        
        # 禁用自动激活默认环境
        print("\n禁用自动激活默认环境")
        ctt = r'''
channels:
  - conda-forge
  - defaults
auto_activate_base: false
'''
        os.makedirs('/etc/conda', exist_ok=True)
        self.newfile(['/etc/conda/.condarc'], ctt)
 
        # 设置自动激活
        #self.setup_conda_auto_activate()
 
        print(f'\n添加 Conda 虚拟环境: {env_name}')
        res = self.open_cmd(f"conda create -n {env_name} python={py_ver} -c conda-forge -y", capout=False, res='out')
        if res['code'] == 0:
            print(f'\n✅ 成功安装虚拟环境: {env_name}')
        
        print("\n✅ 成功安装 Conda")
        return True
    
    def setup_conda_auto_activate(self):
        """设置 Conda 自动激活"""
        print("设置 Conda 自动激活...")
        
        if self.is_windows:
            self.setup_windows_auto_activate()
        else:
            self.setup_unix_auto_activate()

    def setup_windows_auto_activate(self):
        """Windows 系统自动激活设置"""
        print("设置 Windows Conda 自动激活...")
        
        # PowerShell 配置文件路径
        profile_path = os.path.expanduser("~\\Documents\\WindowsPowerShell\\Microsoft.PowerShell_profile.ps1")
        
        # 如果目录不存在则创建
        os.makedirs(os.path.dirname(profile_path), exist_ok=True)
        
        # Conda 自动激活配置
        auto_activate_config = f'''
# Conda 自动激活环境: {env_name}
if (Get-Command conda -ErrorAction SilentlyContinue) {{
    conda activate {env_name}
}}
'''
        try:
            # 检查是否已配置
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = ''
            
            if 'Conda 自动激活环境:' not in content:
                with open(profile_path, 'a', encoding='utf-8') as f:
                    f.write(auto_activate_config)
                print(f"✅ 自动激活已添加到 {profile_path}")
            else:
                print(f"✅ 自动激活已在 {profile_path} 中设置")
                
        except Exception as e:
            print(f"❌ 设置 Windows 自动激活失败: {e}")
            
            # 备选方案：创建批处理文件
            self._create_windows_batch_file()

    def setup_unix_auto_activate(self):
        """Unix 系统自动激活设置"""
        shell_files = [
            os.path.expanduser("~/.bashrc"),
            os.path.expanduser("~/.bash_profile"), 
            os.path.expanduser("~/.zshrc"),
            os.path.expanduser("~/.profile")
        ]
        
        auto_activate_config = f'''
# Conda 自动激活环境: {env_name}
if command -v conda &> /dev/null; then
    conda activate {env_name}
fi
'''
        for shell_file in shell_files:
            if os.path.exists(shell_file) or shell_file.endswith('/.bashrc'):
                try:
                    with open(shell_file, 'r') as f:
                        content = f.read()
                    
                    if 'ryweb Conda 自动激活' not in content:
                        with open(shell_file, 'a') as f:
                            f.write(auto_activate_config)
                        print(f"✅ 自动激活已添加到 {shell_file}")
                    else:
                        print(f"✅ 自动激活已在 {shell_file} 中设置")
                        
                except Exception as e:
                    print(f"❌ 设置 {shell_file} 失败: {e}")

    def install_fastapi(self, new='0'):
        """安装必要的 Python 包: fastapi uvicorn python-multipart rypi"""
        pkgs = "fastapi uvicorn python-multipart rypi"
        print(f"\n安装必要的 Python 包: {pkgs}")
        
        # 首先检查是否存在指定的 conda 虚拟环境
        res = self.open_cmd(f"conda env list | grep {env_name}", capout='eo', res='out')
        
        if res['code'] == 0 and env_name in res['out']:
            # conda 环境存在，使用 conda 环境安装
            res = self.open_cmd(f"conda install -n {env_name} {pkgs} -y", capout=False, res='out')
            
            if res['code'] == 0:
                print(f"\n✅ {pkgs} 安装成功")
            else:
                print(f"⚠️ 安装失败，尝试使用 pip...")
                # 使用 conda run 命令运行 pip
                res = self.open_cmd(f"conda run -n {env_name} pip install {pkgs}", capout=False, res='out')
                if res['code'] == 0:
                    print(f"\n✅ {pkgs} 安装成功")
                else:
                    print(f"\n❌ {pkgs} 安装失败")
        else:
            # conda 环境不存在，使用系统环境的 pip
            print(f"\n⚠️ Conda 虚拟环境 {env_name} 不存在，使用系统虚拟环境的 pip 安装")
            env_path = self.lpath(env_dir, env_name)
            self.install_env()

            # 使用 pip 安装包
            print(f"\n安装 {pkgs}...")
            if self.is_windows:
                res = self.open_cmd(f"{env_path}/Scripts/python -m pip install {pkgs}", capout=False, res='out')
            else:
                res = self.open_cmd(f"{env_path}/bin/python -m pip install {pkgs}", capout=False, res='out')
                
            if res['code'] == 0:
                print(f"\n✅ {pkgs} 安装成功")
                return True
            else:
                print(f"\n❌ {pkgs} 安装失败")
                return False

    def install_env(self, new='0'):
        env_path = self.lpath(env_dir, env_name)
        if os.path.exists(env_path) and new == '1':
            print("\n清理旧的 Conda 安装...")
            try:
                shutil.rmtree(env_path)
            except Exception as e:
                print(f"清理失败: {e}")

        env_cfg = self.lpath(env_path, 'pyvenv.cfg')
        if not os.path.isfile(env_cfg):
            if self.is_linux:
                # 先确保系统支持 venv（仅 Linux 需要）
                if shutil.which('apt'):
                    print("\n安装 python3-venv...")
                    res = self.open_cmd("sudo apt install -y python3-venv", res='out')

            # 创建系统虚拟环境
            print("\n创建系统虚拟环境...")
            res = self.open_cmd(f"python -m venv {env_path}", capout=False, res='out')

            if res['code'] == 0:
                print(f"\n✅ {env_name} 系统虚拟环境创建成功")
            else:
                print(f"\n❌ {env_name} 系统虚拟环境创建失败")
                return False

            if self.is_windows:
                pip_exe = self.lpath(env_path, 'Scripts', 'pip.exe')
                python_exe = self.lpath(env_path, 'Scripts', 'python.exe')
            else:
                pip_exe = self.lpath(env_path, 'bin', 'pip')
                python_exe = self.lpath(env_path, 'bin', 'python')

            # 如果 pip 不存在，用 ensurepip 安装
            if not os.path.exists(pip_exe):
                self.open_cmd(f"{python_exe} -m ensurepip --upgrade", res='out')

    def install_php(self, new='0'):
        """安装 PHP"""
        
        print("\n准备安装 PHP")

        if shutil.which('php') and new=='0':
            res = self.run_cmd('php -v', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split(' ')[1].split('-')[0].strip()
            print(f'\n已存在 PHP, 当前版本: {ver}')
            global php_ver
            php_ver = ver
            return
        
        exts = ['fpm', 'curl', 'gd', 'mbstring', 'xml', 'zip', 'json', 'bcmath', 'sqlite3']
        pkg = ['php'] + [f'php-{ext}' for ext in exts]
        pkg = ' '.join(pkg)

        if self.is_linux:
            if shutil.which('apt'):
                print("\n使用 apt 安装 PHP...")
                # 其它数据库: pgsql,mongodb,redis,memcached
                res = self.open_cmd(f"sudo apt install -y {pkg}", capout=False, res='out')
            elif shutil.which('yum'):
                print("\n使用 yum 安装 PHP...")
                res = self.open_cmd(f"sudo yum install -y {pkg}", capout=False, res='out')
            elif shutil.which('dnf'):
                print("\n使用 dnf 安装 PHP...")
                res = self.open_cmd(f"sudo dnf install -y {pkg}", capout=False, res='out')
            else:
                print("\n无法找到支持的包管理器，跳过 PHP 安装")
                return False
            
            if res['code'] == 0:
                # 将 php-fpm 连接为可执行文件
                self.php_fpm_bin()
            else:
                print(f"\n❌ PHP 安装失败")
                return False
            
        elif self.is_windows:
            pkg_url = php_pkg_win
            filename = os.path.basename(pkg_url)
            filepath = self.download_file(pkg_url, filename)
            if not filepath:
                return False

            print(f"\n正在安装 PHP...")
            app_dir_php = self.lpath(app_dir, f"php-{php_ver}")
            if self.extract_file(filepath, app_dir_php):
                # 将 PHP 目录添加到系统环境变量与环境路径
                if app_dir_php:
                    self.set_env_var_file('RYWEB_PHP_ROOT', app_dir_php)
                    self.add_path_to_env(app_dir_php)
                    #print(f'path: {os.environ.get("PATH", "")}')
                    
        elif self.is_mac:
            res = self.open_cmd(f'brew install {pkg}', capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ PHP 安装失败")
                return False
        else:
            print("未知系统，跳过 PHP 安装")
            return False

        print("\n✅ 成功安装 PHP")
        return True
    
    def php_fpm_bin(self):
        """查找 PHP-FPM 并创建软连接"""
        print("\n🔍 查找 PHP-FPM...")
        
        # 查找 php*-fpm 和 php-fpm*
        cmd = "find /usr/sbin /usr/bin /usr/local/bin -name 'php*-fpm' -o -name 'php-fpm*' 2>/dev/null | head -1"
        res = self.open_cmd(cmd, res='out')
        
        if not res['out']:
            print("❌ 未找到 PHP-FPM")
            return False
        
        path = res['out'].strip()
        print(f"📦 找到: {path}")
        
        # 用 which 验证
        bin = os.path.basename(path)
        res = self.open_cmd(f"which {bin}", res='out')
        
        if res['code'] != 0:
            print(f"❌ which 验证失败: {bin}")
            return False
        
        # 创建软连接
        link = f"sudo ln -sf {path} /usr/local/bin/php-fpm"
        res = self.open_cmd(link, res='out')
        
        if res['code'] == 0:
            print("✅ 软连接创建成功: /usr/local/bin/php-fpm")
            return True
        else:
            print(f"❌ 软连接创建失败:\n{res['err']}")
            return False
        
    def install_certbot(self, new='0'):
        """安装 Certbot"""

        print("\n准备安装 Certbot")

        if shutil.which('certbot') and new=='0':
            res = self.run_cmd('certbot --version', capout='eo')
            ver = '0.0'
            if res.stdout:
                ver = res.stdout.split(' ')[1].strip()
            print(f'\n已存在 Certbot, 当前版本: {ver}')
            global certbot_ver
            certbot_ver = ver
            return

        print(f"\n正在安装 Certbot...")
        if self.is_linux:
            if shutil.which('apt'):
                # Ubuntu/Debian
                res = self.open_cmd("sudo apt install -y certbot python3-certbot-nginx", capout=False, res='out')
            elif shutil.which('yum'):
                # CentOS/RHEL
                res = self.open_cmd("sudo yum install -y certbot python3-certbot-nginx", capout=False, res='out')
            elif shutil.which('dnf'):
                # Fedora
                res = self.open_cmd("sudo dnf install -y certbot python3-certbot-nginx", capout=False, res='out')
            else:
                print("❌ 不支持的 Linux 发行版")
                return False
            
            if res['code'] != 0:
                print(f"\n❌ Certbot 安装失败")
                return False
        
        elif self.is_mac:
            res = self.open_cmd('brew install certbot', capout=False, res='out')
            if res['code'] != 0:
                print(f"\n❌ Certbot 安装失败")
                return False
        
        elif self.is_windows:
            #print("❌ Windows 平台请手动安装 Certbot")
            #print("下载地址: https://certbot.eff.org/instructions")
            
            pkg_url = certbot_pkg_win
            filename = os.path.basename(pkg_url)
            filepath = self.download_file(pkg_url, filename)
            if not filepath:
                return False
            #self.open_cmd(f"pip install {filepath}", capout=False, res='out')

            #self.open_cmd(f"conda install -n {env_name} -c conda-forge certbot", capout=False, res='out')
            #self.open_cmd(f"conda run -n {env_name} pip install certbot", capout=False, res='out')
        
        # 验证安装
        res = self.open_cmd("certbot --version", capout=False, res='out')
        if res['code'] == 0:
            print(f"\n✅ 成功安装 Certbot")
            return True
        else:
            print("\n❌ Certbot 安装失败")
            return False
        
    def set_ssl_cert(self, name, dmlist, email):
        """
        使用 Certbot 为指定域名申请 SSL 证书（仅限非泛域名）
        
        :param name: 主机名，用于修改配置文件和生成 Web 根目录（用于 HTTP-01 验证）
        :param dmlist: 域名列表，例如 "abc.cn www.abc.cn"
        :param email: 联系邮箱

        Certbot 提供的三种不同的验证方式
        1. Nginx Web Server plugin (nginx)
        命令：certbot certonly --nginx -d rymaa.cn -d www.rymaa.cn
        适用情况：如果您正在使用 Nginx 作为 Web 服务器
        工作原理：Certbot 会自动修改 Nginx 配置来完成验证

        2. Standalone
        命令：certbot certonly --standalone -d rymaa.cn -d www.rymaa.cn
        适用情况：如果没有运行 Web 服务器，或者可以临时停止 Web 服务器
        工作原理：Certbot 会启动一个临时的 HTTP 服务器（占用 80 端口）来完成验证

        3. Webroot
        命令：certbot certonly --webroot -w /var/www/ryweb/web/rymaa.cn -d rymaa.cn -d www.rymaa.cn
        适用情况：已经有 Web 服务器在运行，且不想停止服务
        工作原理：Certbot 将验证文件写入指定的网站根目录，通过现有的 Web 服务器完成验证
        """

        if not name:
            raise ValueError("主机名称不能为空")
        
        if not dmlist:
            raise ValueError("域名列表不能为空")
        
        dms = re.split(r'[,;|\s]+', dmlist)

        # 检查是否包含泛域名
        is_wildcard = any(d.startswith('*.') for d in dms)
        if is_wildcard:
            res = self.set_ssl_cert_wildcard(name, dmlist, email)
            return res

        dml = []
        for d in dms:
            d = d.strip()
            if d.startswith('*.'):
                continue
            dml.extend(["-d", d])

        if not email:
            email = 'ryweb@rymaa.cn'
        webroot = f'{web_dir}/{name}'

        cmd = ["certbot", "certonly", "--webroot", "-w", webroot, *dml]

        if email:
            cmd.extend(["--email", email])
        else:
            cmd.append("--register-unsafely-without-email")
        cmd = ' '.join(cmd)

        print(f"\n正在申请证书...")
        res = self.open_cmd(cmd, res='poll')
        if res['code'] == 0:
            print(f"\n✅ 证书申请成功！")
            self._ensure_auto_renewal()
            self.update_ssl_config(name, res['out'])
        else:
            print(f"\n❌ 证书申请失败！")

    def set_ssl_cert_wildcard(self, name, dmlist, email):
        """
        使用 Certbot 为指定域名申请 SSL 证书（支持泛域名）
        
        :param name: 主机名，用于修改配置文件
        :param dmlist: 域名列表，例如 "abc.cn www.abc.cn"
        :param email: 联系邮箱

        --manual：手动模式
        --non-interactive：非交互模式，但缺少必需的 --manual-auth-hook 参数

        使用 --non-interactive 避免用户交互，根据需求选择：
        --keep-until-expiring：保持现有证书（默认）
        --force-renewal：强制更新证书

        或者 stdbuf -o0 certbot ... 禁用输出缓冲
        -o0 - 无缓冲：数据立即输出
        -oL - 行缓冲：遇到换行符时输出
        -o（默认）- 全缓冲：缓冲区满时输出（通常是4KB）
        Linux: stdbuf
        Python: python -u（无缓冲模式） -m certbot ...
        """

        if not name:
            raise ValueError("主机名称不能为空")
        
        if not dmlist:
            raise ValueError("域名列表不能为空")
        
        dms = re.split(r'[,;|\s]+', dmlist)
        dml = []
        for d in dms:
            d = d.strip()
            dml.extend(["-d", d])

        if not email:
            email = 'ryweb@rymaa.cn'
        webroot = f'{web_dir}/{name}'

        cmd = ["certbot", "certonly", "--manual", "--preferred-challenges", "dns", *dml]

        if email:
            cmd.extend(["--email", email])
        else:
            cmd.append("--register-unsafely-without-email")
        cmd = ' '.join(cmd)

        print(f"\n正在申请证书...")
        res = self.open_cmd(cmd, res='poll')
        if res['code'] == 0:
            print(f"\n✅ 证书申请成功！")
            self._ensure_auto_renewal()
            self.update_ssl_config(name, res['out'])
        else:
            print(f"\n❌ 证书申请失败！")

    def _ensure_auto_renewal(self):
        """自动启用自动续期（通常 certbot 已配置好 cron 或 systemd）"""
        # 检查 systemd 定时器（Ubuntu/Debian/CentOS 7+）
        res = self.open_cmd("systemctl is-active certbot.timer", res='out')
        if "active" not in res['out']:
            self.open_cmd("systemctl enable --now certbot.timer", res='out')
            print("\n✅ 已启用 certbot 自动续期定时器")
        else:
            print("\nℹ️ certbot 自动续期已启用")

    def update_ssl_config(self, name, ctt):
        """更新 Nginx SSL 证书配置"""
        
        print(f'\n更新 Nginx SSL 证书配置')
        path = self.lpath(nginx_host_dir, f'{name}.conf')
        if not os.path.exists(path):
            print(f'\n配置文件不存在: {path}')
            return False

        # 提取证书路径
        cert_path = re.search(r'(/[^\s]+fullchain\.pem)', ctt)
        key_path = re.search(r'(/[^\s]+privkey\.pem)', ctt)
        
        if not (cert_path and key_path):
            return False
        
        cert_path = cert_path.group(1).strip()
        key_path = key_path.group(1).strip()
        print(f'\ncert_pem: {cert_path}')
        print(f'\nkey_pem: {key_path}\n')
        
        # 读取并更新配置文件
        with open(path, 'r') as f:
            content = f.read()
        
        # 替换配置
        content = re.sub(r'#*\s*listen 443 ssl;', 'listen 443 ssl;', content)
        content = re.sub(r'#*\s*ssl_certificate\s+.*?;', f'ssl_certificate {cert_path};', content)
        content = re.sub(r'#*\s*ssl_certificate_key\s+.*?;', f'ssl_certificate_key {key_path};', content)
        
        # 写回文件
        with open(path, 'w') as f:
            f.write(content)
        
        return True

    def del_ssl_cert(self, name):
        """删除 SSL 证书"""
        self.open_cmd(f"certbot revoke --cert-name {name}", capout=False, res='out')
        self.open_cmd(f"certbot delete --cert-name {name}", capout=False, res='out')

    def set_pass(self, type, passwd):
        """设置 ArangoDB 数据库登录密码"""
        if not type:
            print('类型不能为空')
            return False

        if not passwd:
            print('密码不能为空')
            return False

        if type == 'adb':
            # 等待服务启动
            print("等待 ArangoDB 服务启动...")
            time.sleep(15)
            
            # 通过 REST API 设置密码
            try:
                url = "http://127.0.0.1:8529/_api/user/root"
                data = {"passwd": passwd}
                
                res = requests.put(
                    url,
                    json=data,
                    auth=('root', ''),  # 初始空密码
                    timeout=30
                )
                
                if res.status_code in [200, 202]:
                    print("✅ ArangoDB 密码设置成功")
                    print(f"   用户名: root")
                    print(f"   密码: {passwd}")
                else:
                    print(f"❌ 密码设置失败: {res.status_code}")
                    
            except Exception as e:
                print(f"❌ 设置密码时出错: {e}")
                print("请手动设置密码或检查服务状态")

    def check_service_status(self, service: str) -> bool:
        """
        检查服务状态。
        """
        if self.is_windows:
            res = self.open_cmd(f'tasklist | findstr /i {service}', res='out')
            return res['code'] == 0 and service in res['out']
            
        else:
            # 使用 ps 检查
            if shutil.which('ps'):
                res = self.open_cmd(f"ps aux | grep {service} | grep -v grep", res='out')
                return res['code'] == 0
            
            # 使用 pgrep 检查
            elif shutil.which('pgrep'):
                res = self.open_cmd(f"pgrep {service}", res='out')
                return res['code'] == 0
            
            else:
                return False
            
    def start_service(self, service):
        """启动服务"""
        svkey = {'nginx': 'Nginx', 'postgres': 'PostgreSQL', 'arangodb': 'ArangoDB', 'seaweedfs': 'SeaweedFS', 'uvicorn': 'Uvicorn', 'php-fpm': 'PHP'}
        svname = self.service_map.get(service, service)
        print(f"\n启动 {svkey.get(svname, svname)}...")

        if svname == 'nginx':
            # 使用自定义配置启动
            nginx_cfg = self.lpath(nginx_cfg_dir, 'nginx.conf')
            if self.is_windows:
                prefix = self.get_env_var_file('RYWEB_NGINX_ROOT')
                cmd = f'nginx -p "{prefix}" -c "{nginx_cfg}"'
                #print(f'cmd: {cmd}')
                res = self.open_cmd(cmd)
                #print(f'res: {res}');exit()
                #wmic process where "name='nginx.exe'" get commandline
            else:
                res = self.open_cmd(f"ps aux | grep apache | grep -v grep", res='out')
                if res['code'] == 0:
                    self.open_cmd(f"pkill -f apache", res='out')
                self.open_cmd(f"nginx -c {nginx_cfg}")

        elif svname == 'postgres':
            if self.is_windows:
                psql_bin = self.get_env_var_file('RYWEB_POSTGRESQL_ROOT')
                pg_ctl = self.lpath(psql_bin, 'pg_ctl.exe')
                initdb = self.lpath(psql_bin, 'initdb.exe')
                psql_conf = os.path.join(psql_dir, "postgresql.conf")
                if not os.path.exists(psql_conf):
                    print("\n数据库初始化...")
                    # -U postgres --auth=trust
                    cmd = f'"{initdb}" -D "{psql_dir}" --encoding=UTF8 --locale=C'
                    res = self.open_cmd(cmd, res='out', capout=False)
                    if res['code'] == 0:
                        print("\n✓ 数据库初始化成功")
                cmd = f'"{pg_ctl}" start -D "{psql_dir}" -l "{psql_dir}/postgresql.log"'
                res = self.open_cmd(cmd)
            elif self.is_mac:
                self.open_cmd('brew services start postgresql')
            else:
                if shutil.which('systemctl'):
                    self.open_cmd('sudo systemctl start postgresql')
                elif shutil.which('service'):
                    self.open_cmd('sudo service postgresql start')

        elif svname == 'arangodb':
            pid_file = self.lpath(adb_dir, 'arangod.pid')
            if os.path.exists(pid_file):
                os.remove(pid_file)

            self.run_cmd(f"arangod --database.directory {adb_data_dir} --database.auto-upgrade true")
            daemon = ' --daemon'
            pidfile = f' --pid-file {adb_dir}/arangod.pid'

            if self.is_windows:
                daemon = ''
                pidfile = ''

            cmd = (
                f"arangod{daemon}{pidfile}"
                f" --log.file {adb_logs_dir}/arangod.log"
                f" --database.directory {adb_data_dir}"
                f" --javascript.app-path {adb_apps_dir}"
                f" --server.endpoint tcp://0.0.0.0:8529"
                f" --server.authentication false"
            )
            self.open_cmd(cmd)

        elif svname == 'seaweedfs':
            cmd = (
                f"weed server -dir={sfs_dir} "
                f"-master.port=9333 -volume.port=8080 "
                f"-filer -filer.port=8888 "
                f"> {sfs_dir}/seaweedfs.log"
            )
            self.open_cmd(cmd)

        elif svname == 'uvicorn':
            cdir = os.getcwd()
            os.chdir(code_dir)

            env_path = self.lpath(env_dir, env_name)
            res = self.open_cmd(f"conda env list | grep {env_name}", capout='eo', res='out')
            if res['code'] == 0 and env_name in res['out']:
                cmd = f"conda run -n {env_name} uvicorn rypi.ryweb.router:app --host 0.0.0.0 --port {proxy_port}"
            else:
                if self.is_windows:
                    cmd = f"{env_path}/Scripts/uvicorn.exe rypi.ryweb.router:app --host 0.0.0.0 --port {proxy_port}"
                else:
                    cmd = f"{env_path}/bin/uvicorn rypi.ryweb.router:app --host 0.0.0.0 --port {proxy_port}"
            res = self.open_cmd(cmd)
            os.chdir(cdir)
        
        elif svname == 'php-fpm':
            if self.is_windows:
                svname = 'php'
                php_root = self.get_env_var_file('RYWEB_PHP_ROOT')
                #cmd = f'{php_root}\php-cgi.exe -b 127.0.0.1:{proxy_port}'
                cmd = f'{php_root}\php.exe -S 0.0.0.0:{proxy_port} "{code_dir}/router.php"'
                self.open_cmd(cmd)
            elif self.is_mac:
                self.open_cmd('brew services start php')
            else:
                # /usr/sbin/php-fpm8.1 --nodaemonize --fpm-config /etc/php/8.1/fpm/php-fpm.conf
                # php-fpm --fpm-config /etc/php/8.1/fpm/php-fpm.conf
                # php-fpm -y /path/to/php-fpm.conf
                # php-fpm -t 2>&1 | head -n 5
                self.open_cmd('php-fpm')

        # 等待并检查状态
        for i in range(10):
            time.sleep(1)
            print(f"正在启动: {i+1}/10", end='\r', flush=True)
            if self.check_service_status(svname):
                print(f"✅ {svkey.get(svname, svname)} 启动成功")
                return True
        
        print(f"❌ {svkey.get(svname, svname)} 启动失败")
        return False
    
    def stop_service(self, service):
        """停止服务"""
        svkey = {'nginx': 'Nginx', 'postgres': 'PostgreSQL', 'arangodb': 'ArangoDB', 'seaweedfs': 'SeaweedFS', 'uvicorn': 'Uvicorn', 'php-fpm': 'PHP'}
        svname = self.service_map.get(service, service)
        print(f"\n停止 {svkey.get(svname, svname)}...")
        
        if svname == 'nginx':
            if self.is_windows:
                self.open_cmd("taskkill /f /im nginx.exe")
            else:
                self.open_cmd("pkill -f nginx")

        elif svname == 'postgres':
            if self.is_windows:
                psql_bin = self.get_env_var_file('RYWEB_POSTGRESQL_ROOT')
                pg_ctl = self.lpath(psql_bin, 'pg_ctl.exe')
                cmd = f'"{pg_ctl}" stop -D "{psql_dir}" -m fast'
                self.open_cmd(cmd)
            elif self.is_mac:
                self.open_cmd('brew services stop postgresql')
            else:
                self.open_cmd('sudo systemctl stop postgresql')

        elif svname == 'arangodb':
            if self.is_windows:
                self.open_cmd("taskkill /f /im arangod.exe")
            else:
                self.open_cmd("pkill -f arangod")
                pid_file = self.lpath(adb_dir, 'arangod.pid')
                if os.path.exists(pid_file):
                    os.remove(pid_file)

        elif svname == 'seaweedfs':
            if self.is_windows:
                self.open_cmd("taskkill /f /im weed.exe")
            else:
                self.open_cmd("pkill -f weed")

        elif svname == 'uvicorn':
            if self.is_windows:
                self.open_cmd("taskkill /f /im uvicorn.exe")
            else:
                self.open_cmd("pkill -f uvicorn")
        
        elif svname == 'php-fpm':
            if self.is_windows:
                svname = 'php'
                self.open_cmd('taskkill /f /im php.exe')
                self.open_cmd('taskkill /f /im php-cgi.exe')
                self.open_cmd('taskkill /f /im php-fpm.exe')
            elif self.is_mac:
                self.open_cmd('brew services stop php')
                self.open_cmd('pkill -f php-fpm')
            else:
                self.open_cmd('sudo pkill -f php-fpm')
                self.open_cmd('sudo pkill -f php-cgi')

        # 等待并检查状态
        for i in range(10):
            time.sleep(1)
            print(f"正在停止: {i+1}/10", end='\r', flush=True)
            if not self.check_service_status(svname):
                print(f"✅ {svkey.get(svname, svname)} 停止成功")
                return True
        
        print(f"❌ {svkey.get(svname, svname)} 停止失败")
        return False
    
    def reload_service(self, service):
        """重启服务"""
        svkey = {'nginx': 'Nginx', 'postgres': 'PostgreSQL', 'arangodb': 'ArangoDB', 'seaweedfs': 'SeaweedFS', 'uvicorn': 'Uvicorn', 'php-fpm': 'PHP'}
        svname = self.service_map.get(service, service)
        print(f"\n重启 {svkey.get(svname, svname)}...")

        if svname == 'nginx':
            # 使用自定义配置重启
            nginx_cfg = self.lpath(nginx_cfg_dir, 'nginx.conf')
            if self.is_windows:
                prefix = self.get_env_var_file('RYWEB_NGINX_ROOT')
                cmd = f'nginx -s reload'
                #print(f'cmd: {cmd}')
                self.open_cmd(cmd)
                #wmic process where "name='nginx.exe'" get commandline
            else:
                res = self.open_cmd(f"ps aux | grep apache | grep -v grep", res='out')
                if res['code'] == 0:
                    self.open_cmd(f"pkill -f apache", res='out')
                self.open_cmd(f"nginx -s reload", capout=False)

        elif svname == 'postgres':
            if self.is_windows:
                psql_bin = self.get_env_var_file('RYWEB_POSTGRESQL_ROOT')
                pg_ctl = self.lpath(psql_bin, 'pg_ctl.exe')
                cmd = f'"{pg_ctl}" stop -D "{psql_dir}" -m fast'
                self.open_cmd(cmd, res='out')
                cmd = f'"{pg_ctl}" start -D "{psql_dir}" -l "{psql_dir}/postgresql.log"'
                self.open_cmd(cmd)
            elif self.is_mac:
                self.open_cmd('brew services restart postgresql')
            else:
                if shutil.which('systemctl'):
                    self.open_cmd('sudo systemctl restart postgresql')
                elif shutil.which('service'):
                    self.open_cmd('sudo service postgresql restart')

        elif svname == 'arangodb':
            pid_file = self.lpath(adb_dir, 'arangod.pid')
            if os.path.exists(pid_file):
                os.remove(pid_file)

            if self.is_windows:
                self.open_cmd("taskkill /f /im arangod.exe", res='out')
                daemon = ''
                pidfile = ''
            else:
                self.open_cmd("pkill -f arangod")
                daemon = ' --daemon'
                pidfile = f' --pid-file {adb_dir}/arangod.pid'

            self.run_cmd(f"arangod --database.directory {adb_data_dir} --database.auto-upgrade true")

            cmd = (
                f"arangod{daemon}{pidfile}"
                f" --log.file {adb_logs_dir}/arangod.log"
                f" --database.directory {adb_data_dir}"
                f" --javascript.app-path {adb_apps_dir}"
                f" --server.endpoint tcp://0.0.0.0:8529"
                f" --server.authentication false"
            )
            self.open_cmd(cmd)

        elif svname == 'seaweedfs':
            if self.is_windows:
                self.open_cmd("taskkill /f /im weed.exe", res='out')
            else:
                self.open_cmd("pkill -f weed")
            cmd = (
                f"weed server -dir={sfs_dir} "
                f"-master.port=9333 -volume.port=8080 "
                f"-filer -filer.port=8888 "
                f"> {sfs_dir}/seaweedfs.log"
            )
            self.open_cmd(cmd)

        elif svname == 'uvicorn':
            cdir = os.getcwd()
            os.chdir(web_dir)

            env_path = self.lpath(env_dir, env_name)
            res = self.open_cmd(f"conda env list | grep {env_name}", capout='eo', res='out')
            if res['code'] == 0 and env_name in res['out']:
                cmd = f"conda run -n {env_name} uvicorn main:app --host 0.0.0.0 --port {proxy_port}"
            else:
                if self.is_windows:
                    self.open_cmd(f"taskkill /f /im {env_path}/Scripts/uvicorn.exe", res='out')
                    cmd = f"{env_path}/Scripts/uvicorn main:app --host 0.0.0.0 --port {proxy_port}"
                else:
                    self.open_cmd("pkill -f uvicorn", res='out')
                    cmd = f"{env_path}/bin/uvicorn main:app --host 0.0.0.0 --port {proxy_port}"
            self.open_cmd(cmd)
            os.chdir(cdir)
        
        elif svname == 'php-fpm':
            if self.is_windows:
                self.open_cmd('taskkill /f /im php-cgi.exe', res='out')
                self.open_cmd('taskkill /f /im php-fpm.exe', res='out')
                self.open_cmd('start php-fpm')
            elif self.is_mac:
                self.open_cmd('brew services restart php')
            else:
                # /usr/sbin/php-fpm8.1 --nodaemonize --fpm-config /etc/php/8.1/fpm/php-fpm.conf
                # php-fpm --fpm-config /etc/php/8.1/fpm/php-fpm.conf
                # php-fpm -y /path/to/php-fpm.conf
                # php-fpm -t 2>&1 | head -n 5
                self.open_cmd('systemctl restart php-fpm')

        # 等待并检查状态
        for i in range(10):
            time.sleep(1)
            print(f"正在重启: {i+1}/10", end='\r', flush=True)
            if self.check_service_status(svname):
                print(f"✅ {svkey.get(svname, svname)} 重启成功")
                return True
        
        print(f"❌ {svkey.get(svname, svname)} 重启失败")
        return False
    
    def mdf_mode(self, run_mode):
        """修改运行模式"""
        apps = app_list.get(run_mode)
        if not apps:
            print('未知模式类型')
            return
        self.set_env_var_file('RYWEB_RUN_MODE', run_mode)
        print(f'\n运行模式已修改为: {run_mode}')

    def ins_pkg(self, name, up, ori):
        """安装依赖包"""
        if not name:
            print('\n请指定包名')
            return
        
        s1 = name[0]
        code_dir = name[1:]
        if s1 == '.':
            cmd = f'pip install -e {code_dir}'
        else:
            if up:
                up = ' --upgrade'
            else:
                up = ''
                
            if ori:
                if ori == '1':
                    ori = 'https://pypi.org/simple'
                ori = f' -i {ori}'
            else:
                ori = ''
            cmd = f'pip install{up} {name}{ori}'
        
        # 首先检查是否存在指定的 conda 虚拟环境
        res = self.open_cmd(f"conda env list | grep {env_name}", capout='eo', res='out')
        
        if res['code'] == 0 and env_name in res['out']:
            # conda 环境存在，使用 conda 环境安装
            print(f"⚠️ 安装失败，尝试使用 pip...")
            # 使用 conda run 命令运行 pip
            res = self.open_cmd(f"conda run -n {env_name} {cmd}", capout=False, res='out')
            if res['code'] == 0:
                print(f"\n✅ {name} 安装成功")
            else:
                print(f"\n❌ {name} 安装失败")
        else:
            # conda 环境不存在，使用系统环境的 pip
            print(f"\n⚠️ Conda 虚拟环境 {env_name} 不存在，使用系统虚拟环境的 pip 安装")

            env_path = self.lpath(env_dir, env_name)
            # 使用 pip 安装包
            print(f"\n安装 {name}: {cmd}")
            if self.is_windows:
                res = self.open_cmd(f"{env_path}/Scripts/python -m {cmd}", capout=False, res='out')
            else:
                res = self.open_cmd(f"{env_path}/bin/python -m {cmd}", capout=False, res='out')
                
            if res['code'] == 0:
                print(f"\n✅ {name} 安装成功")
                return True
            else:
                print(f"\n❌ {name} 安装失败")
                return False

    def unins_pkg(self, name):
        """卸载依赖包"""
        if not name:
            print('\n请指定包名')
            return
        
        cmd = f'pip uninstall {name} -y'
        
        # 首先检查是否存在指定的 conda 虚拟环境
        res = self.open_cmd(f"conda env list | grep {env_name}", capout='eo', res='out')
        
        if res['code'] == 0 and env_name in res['out']:
            # conda 环境存在，使用 conda 环境卸载
            print(f"⚠️ 安装失败，尝试使用 pip...")
            # 使用 conda run 命令运行 pip
            res = self.open_cmd(f"conda run -n {env_name} {cmd}", capout=False, res='out')
            if res['code'] == 0:
                print(f"\n✅ {name} 卸载成功")
            else:
                print(f"\n❌ {name} 卸载失败")
        else:
            # conda 环境不存在，使用系统环境的 pip
            print(f"\n⚠️ Conda 虚拟环境 {env_name} 不存在，使用系统虚拟环境的 pip 卸载")

            env_path = self.lpath(env_dir, env_name)
            # 使用 pip 卸载包
            print(f"\n卸载 {name}: {cmd}")
            if self.is_windows:
                res = self.open_cmd(f"{env_path}/Scripts/python -m {cmd}", capout=False, res='out')
            else:
                res = self.open_cmd(f"{env_path}/bin/python -m {cmd}", capout=False, res='out')
                
            if res['code'] == 0:
                print(f"\n✅ {name} 卸载成功")
                return True
            else:
                print(f"\n❌ {name} 卸载失败")
                return False

    def add_host(self, name, dmlist):
        """添加主机"""
        print(f"\n添加主机: {name}, 域名: {dmlist}")
        
        # 创建主机目录
        host_dir = self.lpath(web_dir, name)
        os.makedirs(host_dir, exist_ok=True)
        
        # 创建网站默认首页
        self.newfile([host_dir, 'index.html'], index_ctt)

        # 创建网站管理员页面
        self.newfile([host_dir, 'admin.html'], admin_ctt)

        # 创建 40X 错误页面
        self.newfile([host_dir, '40x.html'], err_40x_ctt)

        # 创建 50X 错误页面
        self.newfile([host_dir, '50x.html'], err_50x_ctt)

        # 创建 Nginx 虚拟主机配置
        ctt = self.restr(host_conf, domain_list=dmlist, proxy_port=f'{proxy_port}', code_dir=code_dir, web_dir=web_dir, host_dir=host_dir, host_name=name)
        self.newfile([nginx_cfg_dir, 'vhost', f'{name}.conf'], ctt)
        
        self.run_cmd(f'sudo chown -R {www_user}:{www_user} {host_dir}')
        self.run_cmd(f'sudo chmod -R 755 {host_dir}')

        print(f"\n✅ 主机 {name} 添加成功")
        
        # 重新加载 Nginx
        if self.check_service_status('nginx'):
            self.open_cmd("nginx -s reload")
    
    def del_host(self, name):
        """删除主机"""
        print(f"删除主机: {name}")
        
        # 删除主机目录
        host_dir = self.lpath(web_dir, name)
        if os.path.exists(host_dir):
            shutil.rmtree(host_dir)
        
        # 删除 Nginx 虚拟主机配置
        vhost_file = self.lpath(cfg_dir, 'nginx', 'vhost', f'{name}.conf')
        if os.path.exists(vhost_file):
            os.remove(vhost_file)
        
        print(f"✅ 主机 {name} 删除成功")
        
        # 重新加载 Nginx
        if self.check_service_status('nginx'):
            self.open_cmd("nginx -s reload")

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

    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # install 命令
    install_parser = subparsers.add_parser('install', help='安装网站环境管理器')
    install_parser.add_argument('-p', '--path', help='安装目录路径')
    install_parser.add_argument('-m', '--mode', help='运行模式')
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='启动服务')
    start_parser.add_argument('service', nargs='?', help='服务名称 (ngi, psql, adb, sfs, uvi, php)')
    
    # stop 命令
    stop_parser = subparsers.add_parser('stop', help='停止服务')
    stop_parser.add_argument('service', nargs='?', help='服务名称 (ngi, psql, adb, sfs, uvi, php)')
    
    # reload 命令
    reload_parser = subparsers.add_parser('reload', help='重启服务')
    reload_parser.add_argument('service', nargs='?', help='服务名称 (ngi, psql, adb, sfs, uvi, php)')
    
    # mode 命令
    mode_parser = subparsers.add_parser('mode', help='修改运行模式')
    mode_parser.add_argument('mode', nargs='?', help='模式类型 (npp, nfp, nfpc...)')
    
    # app 命令
    app_parser = subparsers.add_parser('app', help='安装服务应用')
    app_parser.add_argument('service', nargs='?', help='应用名称 (ngi, psql, adb, sfs, uvi, php, cer)')
    app_parser.add_argument('-i', '--isnew', default='0', help='是否全新安装，0=否，1=是')
    
    # pkg 命令
    pkg_parser = subparsers.add_parser('pkg', help='安装依赖包')
    pkg_parser.add_argument('-n', '--name', help='依赖包名')
    pkg_parser.add_argument('-u', '--update', action='store_true', help='升级安装')
    pkg_parser.add_argument('-o', '--origin', help='仓库源')
    
    # pkg 命令
    unpkg_parser = subparsers.add_parser('unpkg', help='卸载依赖包')
    unpkg_parser.add_argument('-n', '--name', help='依赖包名')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加主机')
    add_parser.add_argument('-n', '--name', required=True, help='主机名称')
    add_parser.add_argument('-d', '--dmlist', required=True, help='域名列表')
    
    # del 命令
    del_parser = subparsers.add_parser('del', help='删除主机')
    del_parser.add_argument('-n', '--name', required=True, help='主机名称')
    
    # ssl 命令
    ssl_parser = subparsers.add_parser('ssl', help='设置 SSL 证书')
    ssl_parser.add_argument('-n', '--name', required=True, help='主机名称')
    ssl_parser.add_argument('-d', '--dmlist', required=True, help='域名列表')
    ssl_parser.add_argument('-e', '--email', help='邮箱地址')
    
    # ssldel 命令
    ssldel_parser = subparsers.add_parser('ssldel', help='删除 SSL 证书')
    ssldel_parser.add_argument('-n', '--name', required=True, help='主机名称')
    
    # pass 命令
    pass_parser = subparsers.add_parser('pass', help='设置指定类型的密码')
    pass_parser.add_argument('-t', '--type', required=True, help='修改类型')
    pass_parser.add_argument('-p', '--passwd', required=True, help='新密码')
    
    args = parser.parse_args(args)
    
    ryweb = RyWeb()
    global www_root, run_mode, apps
    wwwroot1 = ryweb.get_env_var_file('RYWEB_WWW_ROOT')
    if wwwroot1:
        www_root = wwwroot1
        ryweb.mkdir()

    run_mode1 = ryweb.get_env_var_file('RYWEB_RUN_MODE')
    if run_mode1:
        run_mode = run_mode1
    if not run_mode:
        run_mode = 'nfp'
    apps = app_list.get(run_mode)
    if not apps:
        run_mode = 'nfp'
        apps = app_list.get(run_mode)
        ryweb.set_env_var_file('RYWEB_RUN_MODE', run_mode)
    ryweb.chsv()

    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.help:
        print(HELP)

    elif args.command == 'install':
        # 设置安装路径
        if args.path:
            www_root = args.path
        
        if args.mode:
            run_mode = args.mode
            apps = app_list[run_mode]
            if not apps:
                run_mode = 'nfp'
                apps = app_list[run_mode]
                ryweb.chsv()

        ryweb.mkdir()
        print(f"\n安装 ryweb 到: {www_root}\n")
        
        # 安装所有组件
        if ryweb.is_linux:
            if shutil.which('apt'):
                # Debian/Ubuntu/Mint/Kali
                ryweb.open_cmd("sudo apt update", capout=False, res='out')
            elif shutil.which('yum'):
                # RedHat/CentOS/Fedora/openSUSE
                ryweb.open_cmd("sudo yum install -y epel-release", capout=False, res='out')
        elif ryweb.is_mac:
            if not shutil.which('brew'):
                res = ryweb.open_cmd('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', capout=False, res='out')
                res = ryweb.open_cmd('brew update', capout=False, res='out')
        
        for app in apps:
            func = getattr(ryweb, f'install_{app}', None)
            if func:
                func()
        
        # 创建安装信息页面
        ctt = ryweb.restr(install_ctt, www_root=www_root, www_user=www_user, proxy_port=f'{proxy_port}', admin_port=f'{admin_port}')
        ryweb.newfile([web_dir, 'index.html'], ctt)
        ryweb.set_env_var_file('RYWEB_WWW_ROOT', www_root)
        ryweb.set_env_var_file('RYWEB_RUN_MODE', run_mode)
        
        print("\n✅ ryweb 安装完成")
        print("\n可使用 rypi ryweb -H 查看帮助\n")
        
    elif args.command == 'start':
        if args.service:
            ryweb.start_service(args.service)
        else:
            # 启动所有服务
            for service in ryweb.service_map.keys():
                ryweb.start_service(service)
    
    elif args.command == 'stop':
        if args.service:
            ryweb.stop_service(args.service)
        else:
            # 停止所有服务（逆序）
            for service in reversed(list(ryweb.service_map.keys())):
                ryweb.stop_service(service)
    
    elif args.command == 'reload':
        if args.service:
            ryweb.reload_service(args.service)
        else:
            # 重启所有服务
            for service in ryweb.service_map.keys():
                ryweb.reload_service(service)
    
    elif args.command == 'mode':
        if args.mode:
            ryweb.mdf_mode(args.mode)
    
    elif args.command == 'app':
        if args.service:
            n = ryweb.appmap.get(args.service, args.service)
            func = getattr(ryweb, f'install_{n}', None)
            if func:
                func(args.isnew)
            else:
                print(f'\n未知服务应用: {n}')
    
    elif args.command == 'pkg':
        ryweb.ins_pkg(args.name, args.update, args.origin)
    
    elif args.command == 'unpkg':
        ryweb.unins_pkg(args.name)
    
    elif args.command == 'add':
        ryweb.add_host(args.name, args.dmlist)
    
    elif args.command == 'del':
        ryweb.del_host(args.name)
    
    elif args.command == 'ssl':
        ryweb.set_ssl_cert(args.name, args.dmlist, args.email)

    elif args.command == 'ssldel':
        ryweb.del_ssl_cert(args.name)

    elif args.command == 'pass':
        ryweb.set_pass(args.type, args.passwd)

    else:
        print(HELP)

if __name__ == '__main__':
    main()