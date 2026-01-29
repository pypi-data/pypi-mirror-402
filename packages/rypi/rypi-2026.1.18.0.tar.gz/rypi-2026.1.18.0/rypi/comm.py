#!/usr/bin/env python
'''
锐派的常用/共用函数(Common Function)，模块调用或命令行调用均可。
'''

VER = r'''
comm version: 2026.1.15.0
'''

COPR = r'''
版权所有 2025 锐码[rymaa.cn] - rymaa_cn@163.com 本软件采用 锐码署名传播许可证(RSPL) 授权。详情请见 LICENSE 或 LICENSE-EN 文件。
'''

INFO = r'''
锐派的常用/共用函数(Common Function)。
可通过模块调用，也可通过命令行调用。
包含一些实用函数，如：rstr，b64，md5，sha
'''

HELP = r'''
+-------------------------------------------+
|           RyPi Common Functions           |
+-------------------------------------------+
|            HomePage: rymaa.cn             |
+-------------------------------------------+

Usage:
    rypi comm [option]

Options:
    -H, --help   Show help / 显示帮助
    -I, --info   Show info / 显示信息
    -C, --copr   Show copyright / 显示版权
    -V, --version   Show version / 显示版本
    -h, --func_help   Show function help / 显示指定函数的帮助信息
    -f, --func   Show all function / 显示所有函数
    -r, --run   run function / 运行指定的函数
    -p, --para   function parameter / 运行函数的参数列表，多参数需要加引号
'''

##############################

import os
import sys
import argparse
import importlib
import importlib.util
import secrets
import string
import base64
import json
import re
import hashlib
import pkgutil
from pathlib import Path
import inspect
import shlex

##############################

def _load(mname):
    '''
    载入指定名称的模块。
    返回: void
    参数列表：
        mname (str): 模块名（不含后缀，可以与包名组合）
    '''

    mod = importlib.import_module(mname)
    return mod

def _loadp(path):
    '''
    载入指定路径的模块。
    返回: void
    参数列表：
        path (str): 模块路径（包含后缀）
    '''

    name = path.replace('/', '_').replace('.', '_')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def vdump(var, indent=0):
    '''
    打印指定变量的属性，支持缩进控制。
    返回: void
    参数列表：
        var (str): 变量名称
        indent (int): 缩进
    '''

    if isinstance(var, dict):
        print(' ' * indent + 'array({})'.format(len(var)))
        for key, value in var.items():
            print(' ' * (indent + 2) + f'[{repr(key)}] => ', end='')
            vdump(value, indent + 4)
    elif isinstance(var, list):
        print(' ' * indent + f'array({len(var)})')
        for item in var:
            print(' ' * (indent + 2) + '[{}] => '.format(var.index(item)), end='')
            vdump(item, indent + 4)
    else:
        print(f'{type(var).__name__}({repr(var)})')

def _get_modules(pkg):
    '''
    获取当前目录下所有命令模块（目录）与辅助模块（.py 文件）。
    返回: 模块元组列表[(mod_name, mod_desc, is_pkg)]
    参数列表：
        pkg (str): 包名（package name）
    '''

    smod = []  # sub module
    spec = importlib.util.find_spec(pkg)
    if spec is None:
        raise ImportError(f"无法找到包: {pkg}")
    if spec.submodule_search_locations is None:
        raise NotADirectoryError(f"{pkg} 不是一个包（无子模块）")
    path = Path(spec.submodule_search_locations[0])

    for _, name, is_pkg in pkgutil.iter_modules([str(path)]):
        if name == 'conf':
            continue
        if is_pkg:
            mod = _load(f'{pkg}.{name}.main')
        else:
            mod = _load(f'{pkg}.{name}')
        doc = inspect.getdoc(mod)
        desc = doc.split('\n')[0].strip() if doc else '无描述'
        smod.append((name, desc, is_pkg))

    return smod

def _get_functions(mod):
    '''
    获取模块中所有函数名（排除 _ 开头的私有函数）。
    返回: 函数元组列表[(func_name, func_desc)]
    参数列表：
        mod (str): 模块（module name）
    '''

    no_func = ['main', 'load', 'loadp', 'get_modules', 'get_functions', 'parse_args', 'run_mod']
    func = [
        (name, (inspect.getdoc(obj) or '无描述').split('\n')[0].strip()) for name, obj in inspect.getmembers(mod, inspect.isfunction)
        if not name.startswith('_') and name not in no_func
    ]
    return func

def _parse_args(args):
    '''
    解析如 "arg1 arg2 'with space' --flag" 的字符串
    返回: 列表[str]
    参数列表：
        args (str): 参数列表（args string）
    '''

    res = {}
    args = args.strip()
    if not args:
        return res
    
    if '=' not in args:
        return shlex.split(args)
    
    # 使用 shlex 分词，支持引号
    lexer = shlex.shlex(args, posix=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    
    for tk in tokens:
        if '=' not in tk:
            raise ValueError(f"无效的键值对: {tk}")
        key, value = tk.split('=', 1)
        res[key] = value
    
    return res

def _run_mod(pkg, mname, cmod, args):
    '''
    加载模块并运行 main 函数。
    返回: void
    参数列表：
        pkg (str): 包名（package name）
        mname (str): 包名（module name）
        cmod (bool): 是否命令模块（is command module）
        args (list): 参数列表
    '''

    #print(f"pkg: {pkg}, mname: {mname}, cmod: {cmod}, args: {args}")
    
    try:
        if cmod:
            # 命令模块: rypi.ryto.main
            mname = f"{pkg}.{mname}.main"
        else:
            # 辅助模块: rypi.util
            mname = f"{pkg}.{mname}"

        mod = _load(mname)
        if hasattr(mod, 'main'):
            return mod.main(args)
        else:
            print(f"模块 {mname} 缺少 main() 函数")
    except Exception as e:
        print(f"加载模块失败: {e}")

def obj(data='', type=1, char='`', indent=0):
    '''
    根据模式标志 type 对输入 data 进行解析或序列化，支持 JSON、自定义编码格式等。

    函数原型:
        obj(data: any = '', type: int = 1, char: any = '`', indent: int = 0) -> any

    返回值:
        - 当 type == 1 时：返回解析后的 dict 或原始对象（若已是 dict），或 None/{}（根据输入合法性）
        - 当 type != 1 时：返回字符串形式的序列化结果，或空字符串（若输入无效）

    参数列表:
        data (any): 输入数据，可以是字符串、字典、数字或其他类型
        type (int): 操作模式标志：
            - 1 : 解析模式（从字符串还原为对象）
            - 其他值 : 序列化模式（将对象转为字符串）
        char (any): 
            - 在解析模式（type == 1）中：用作字段分隔符（默认 '`'）
            - 在序列化模式（type != 1）中：
                - 若为 1：使用 JSON 序列化
                - 若为 2：使用自定义 cts 函数序列化
                - 否则：用作键值对之间的连接分隔符（必须为字符串）
        indent (int): 缩进位数，仅在序列化模式且 char == 2 时传给 cts 函数

    使用示例1（解析 JSON 字符串）:
        obj('{"name":"Alice","age":30}', 1) → {'name': 'Alice', 'age': 30}

    使用示例2（解析自定义编码字符串）:
        obj('a1`b2', 1, '`') → {'a1': 'b2'}

    使用示例3（序列化为自定义字符串）:
        obj({'x': 'y', 'p': 'q'}, 0, '|') → 'x|y|p|q'

    使用示例4（序列化为 JSON）:
        obj({'ok': True}, 0, 1) → '{"ok": true}'

    注意:
        - 依赖外部函数 e36（编码/解码）、stc（处理 '.,' 前缀）、cts（自定义序列化）
        - 当 type != 1 且 char 不为 1 或 2 时，char 必须为字符串，否则会引发 AttributeError
        - 非 dict 对象在序列化模式下会返回空字符串
        - 此函数需与配套的 e36/stc/cts 实现一同使用
    '''

    if type == 1:
        if isinstance(data, dict):
            return data
        if not data or not isinstance(data, str):
            return None
        data = data.strip()
        a = data[:2]
        if a == '{"':
            import json
            return json.loads(data)
        if a == '.,':
            return sto(data)
        a = data.split(char)
        l = len(a)
        o = {}
        for z in range(0, l, 2):
            k = e36(a[z], 2)
            v = e36(a[z + 1], 2) if z + 1 < l else None
            if not k:
                continue
            o[k] = v
        return o
    
    else:
        if isinstance(data, str):
            return data
        if isinstance(data, (int, float)):
            return str(data)
        if not data or not isinstance(data, dict):
            return ''
        if char == 1:
            return json.dumps(data)
        if char == 2:
            return ots(data, indent)
        s = []
        for z in data:
            s.append(e36(z, 1))
            s.append(e36(data[z], 1))
        return char.join(s)

# comma period object
def cpo(data='', type=1, indent=0):
    '''
    使用逗点对象格式进行对象与字符串互换。
    
    函数原型:
        cpo(data: any = '', type: int = 1, indent: int = 0) -> any

    返回值:
        - 当 type == 1 时：返回解析后的 dict 或原始对象（若已是 dict），或 None/{}（根据输入合法性）
        - 当 type != 1 时：返回字符串形式的序列化结果，或空字符串（若输入无效）
        - 可以对下列两种数据进行互换
        - 对象：{'a': 1, 'b':2, 'c':3, 'd':4, 'e':{'aa':11, 'bb':22, 'cc':33}, 'f':[1, 2, 3, {'aaa':111, 'bbb':222, 'ccc':333}, {'aaaa':1111, 'bbbb':2222, 'cccc':3333}, [4, 5, 6]]}
        - CPO 字串：., .a 1 .b 2 .c 3 .d 4 .e ., .aa 11 .bb 22 .cc 33 ,. .f .., 1, 2, 3, ., .aaa 111 .bbb 222 .ccc 333 ,. ., .aaaa 1111 .bbbb 2222 .cccc 3333 ,. .., 4, 5, 6 ,,. ,,. ,.

    参数列表:
        data (any): 输入数据，可以是字符串、字典、数字或其他类型
        type (int): 操作模式标志：
            - 1 : 解析模式（从字符串还原为对象）
            - 其他值 : 序列化模式（将对象转为字符串）
        indent (int): 缩进位数，仅在序列化模式且 char == 2 时传给 cts 函数

    使用示例1（解析 CPO 格式的字符串为对象）:
        cpo('., .name Alice .age 30 ,.', 1) → {'name': 'Alice', 'age': 30}

    使用示例2（将对象序列化为 CPO 字符串）:
        cpo({'x': 'y', 'p': 'q'}, 0) → '., .x y .p q ,.'
    '''

    if type == 1:
       return sto(data)
    return ots(data, indent)

def sto(s=''):
    '''
    将 CPO 格式字符串（comma-period object）解析为对象。

    CPO 是一种紧凑的序列化格式，使用 ., 表示对象开始，.., 表示数组开始，
    ,. 表示对象结束，,,. 表示数组结束。键以 .key 形式出现。

    支持类型：bool（TRUE/FALSE）、null（NULL）、int、float、str、dict、list。

    参数列表:
        s (str): 输入字符串，用于转换为 CPO 对象

    示例:
        sto("., .name Alice .age 30 ,.") → {'name': 'Alice', 'age': 30}
        sto("., .flag TRUE .score 95.5 ,.") → {'flag': True, 'score': 95.5}
        sto("., .tags ..,apple,banana,,. ,.") → {'tags': ['apple', 'banana']}

    注意:
        - 键必须紧跟在 '.' 后，中间不能有空格
        - 值的边界由下一个 ".key" 或结束标记决定
        - 空值用 EMPTY 或空字符串表示
    '''

    if not isinstance(s, str):
        return {}
    
    i = [0]  # 使用列表模拟引用传递
    n = len(s)

    def skip_whitespace():
        while i[0] < n and s[i[0]] in ' \t\n\r':
            i[0] += 1

    def peek_str(length):
        if i[0] + length > n:
            return ''
        return s[i[0]:i[0] + length]

    def parse_value():
        skip_whitespace()
        if i[0] >= n:
            return None

        # 结构类型优先
        if peek_str(3) == '..,':
            i[0] += 3
            return parse_array()
        if peek_str(2) == '.,':
            i[0] += 2
            return parse_object()

        # 普通值：读取直到遇到明确边界
        start = i[0]
        while i[0] < n:
            char = s[i[0]]

            # 如果遇到空格，检查后面是否是新键（.key）
            if char in ' \t\n\r':
                j = i[0]
                while j < n and s[j] in ' \t\n\r':
                    j += 1
                if j < n and s[j] == '.' and j + 1 < n and s[j + 1] not in ' .,\t\n\r':
                    break  # 新键开始，当前值结束

            # 遇到数组结束或逗号（在数组上下文中）
            if peek_str(3) == ',,.' or char == ',':
                break

            i[0] += 1

        val_str = s[start:i[0]].strip()
        if not val_str:
            return ""

        if val_str == "TRUE":
            return True
        elif val_str == "FALSE":
            return False
        elif val_str == "NULL":
            return None
        elif val_str == "EMPTY":
            return ""
        elif val_str.lstrip('-').isdigit():
            return int(val_str)
        else:
            try:
                if '.' in val_str:
                    return float(val_str)
                else:
                    return int(val_str)
            except ValueError:
                return val_str

    def parse_object():
        obj = {}
        skip_whitespace()

        while i[0] < n:
            skip_whitespace()
            if i[0] >= n:
                break

            # 对象结束
            if peek_str(2) == ',.':
                i[0] += 2
                return obj

            # 必须是 '.'，且前面是空白或开头
            if s[i[0]] != '.':
                i[0] += 1
                continue

            # 检查 '.' 前是否为合法位置（开头或空白）
            if i[0] > 0 and s[i[0] - 1] not in ' \t\n\r':
                i[0] += 1
                continue

            i[0] += 1  # 跳过 '.'

            # 提取 key
            if i[0] >= n or s[i[0]] in ' .,\t\n\r':
                continue  # 空 key

            key_start = i[0]
            while i[0] < n and s[i[0]] not in ' .,\t\n\r':
                i[0] += 1
            key = s[key_start:i[0]]
            if not key:
                continue

            skip_whitespace()
            if i[0] >= n:
                obj[key] = ""
                break

            # 解析值
            if peek_str(3) == '..,':
                i[0] += 3
                value = parse_array()
            elif peek_str(2) == '.,':
                i[0] += 2
                value = parse_object()
            else:
                value = parse_value()

            obj[key] = value
            skip_whitespace()

        return obj

    def parse_array():
        arr = []
        skip_whitespace()

        while i[0] < n:
            skip_whitespace()
            if i[0] >= n:
                break

            # 数组结束
            if peek_str(3) == ',,.':
                i[0] += 3
                return arr

            if s[i[0]] == ',':
                i[0] += 1
                continue

            # 解析元素
            if peek_str(3) == '..,':
                i[0] += 3
                value = parse_array()
            elif peek_str(2) == '.,':  # 允许数组中包含对象
                i[0] += 2
                value = parse_object()
            else:
                value = parse_value()

            arr.append(value)
            skip_whitespace()

        return arr

    # 主入口
    skip_whitespace()
    if peek_str(2) == '.,':
        i[0] += 2
        return parse_object()
    return {}

def ots(obj, indent=0):
    '''
    将 Python 对象序列化为 CPO（Comma-Period Object）格式字符串。

    CPO 格式规则：
      - 对象以 "., ... ,." 包裹
      - 数组以 ".., ... ,,." 包裹
      - 键以 ".key value" 形式表示
      - 基础类型映射：True→'TRUE', False→'FALSE', None→'NULL', ''→'EMPTY'
      - 若 indent > 0，则使用换行和缩进；否则用空格分隔

    参数列表:
        obj (object): 输入对象，用于转换为 CPO 格式的字符串
        indent (int): 缩进位数

    示例:
        ots({"name": "Alice", "age": 30}) 
        → "., .name Alice .age 30 ,."

        ots({"ok": True, "list": ["a", "b"]}, indent=2)
        → ".,\n  .ok TRUE\n  .list ..,\n    a,\n    b\n  ,,.\n,."

    注意:
        - 忽略函数类型的值
        - 仅处理 dict 和 list 容器
        - 字符串若为空则输出 'EMPTY'
    '''

    indent = int(indent)
    n = '\n' if indent else ' '

    def pc(char, count):
        """Helper: repeat char `count` times (like ' '.repeat(count))"""
        return char * count

    def arr2str(A, B=0, C=' '):
        a = []
        l = B
        n_inner = C
        for z in range(len(A)):
            v = A[z]
            t = type(v).__name__

            if t == 'function':
                continue
            elif isinstance(v, list):
                prefix = pc(' ', (l + 1) * indent) + '..,'
                s = arr2str(v, l + 1, n_inner) + n_inner + pc(' ', (l + 1) * indent) + ',,.'
                a.append(prefix)
                a.append(s)
            elif isinstance(v, dict):
                prefix = pc(' ', (l + 1) * indent) + '.,'
                s = obj2str(v, l + 1, n_inner) + n_inner + pc(' ', (l + 1) * indent) + ',.'
                a.append(prefix)
                a.append(s)
            else:
                if v is None:
                    v = 'NULL'
                elif isinstance(v, str) and v == '':
                    v = 'EMPTY'
                elif isinstance(v, bool):
                    v = 'TRUE' if v else 'FALSE'
                # 数组元素末尾加逗号（非最后一个）
                if z < len(A) - 1:
                    e = ','
                else:
                    e = ''
                line = pc(' ', (l + 1) * indent) + str(v) + e
                a.append(line)
        return n_inner.join(a)

    def obj2str(A, B=0, C=' '):
        a = []
        l = B
        n_inner = C
        for k in A:
            v = A[k]
            t = type(v).__name__

            if t == 'function':
                continue
            elif isinstance(v, list):
                prefix = pc(' ', (l + 1) * indent) + '.' + str(k) + ' ..,'
                s = arr2str(v, l + 1, n_inner) + n_inner + pc(' ', (l + 1) * indent) + ',,.'
                a.append(prefix)
                a.append(s)
            elif isinstance(v, dict):
                prefix = pc(' ', (l + 1) * indent) + '.' + str(k) + ' .,'
                s = obj2str(v, l + 1, n_inner) + n_inner + pc(' ', (l + 1) * indent) + ',.'
                a.append(prefix)
                a.append(s)
            else:
                if v is None:
                    v = 'NULL'
                elif isinstance(v, str) and v == '':
                    v = 'EMPTY'
                elif isinstance(v, bool):
                    v = 'TRUE' if v else 'FALSE'
                line = pc(' ', (l + 1) * indent) + '.' + str(k) + ' ' + str(v)
                a.append(line)
        return n_inner.join(a)

    # 构建顶层字符串
    body = obj2str(obj, 0, n)
    closing_indent = pc(' ', 0 * indent)  # l=0, so 0 spaces
    result = '.,' + n + body + n + closing_indent + ',.'
    return result

def rstr(type: str = 'lun', len: int = 8) -> str:
    '''
    生成指定类型和长度的随机字符串。

    函数原型:
        rstr(type: str, len: int) -> str

    返回值:
        str: 生成的随机字符串

    参数列表:
        type (str): 字符集类型，可选值：
            - 'l'  : 小写字母（a-z）
            - 'u'  : 大写字母（A-Z）
            - 'n'  : 数字（0-9）
            - 'lu' : 小写 + 大写
            - 'ln' : 小写 + 数字
            - 'un' : 大写 + 数字
            - 'lun': 小写 + 大写 + 数字
        len (int): 随机字符串长度，必须 > 0，默认为 8

    使用示例1:
        rstr('lu', 6) → 可能返回 "Ab3XyZ"

    使用示例2:
        rstr('n', 4) → 可能返回 "7291"

    注意:
        - 如果 type 不在支持列表中，抛出 ValueError
        - len 必须是正整数
    '''

    len = int(len)

    # 构建字符集
    chars = ''
    if 'l' in type:
        chars += string.ascii_lowercase
    if 'u' in type:
        chars += string.ascii_uppercase
    if 'n' in type:
        chars += string.digits

    if not chars:
        raise ValueError("type 必须包含 l, u, n 中至少一个")

    if len < 1:
        raise ValueError("len 必须大于 0")

    if hasattr(secrets, 'choices'):
        res = ''.join(secrets.choices(chars, k=len))
    else:
        res = ''.join(secrets.choice(chars) for _ in range(len))
    return res

def e36(A, B=1):
    """
    对字符串进行自定义的特殊符号编码或解码。
    
    该函数将36个特定的特殊符号和空白字符（如 !@#$%^&* 等）映射为以 '!' 开头的编码形式（如 !1, !2...!a...），
    用于对字符串中的这些符号进行转义（编码）或还原（解码）。
    
    编码过程：
        1. 将输入字符串中的 '!' 替换为 ':E:' 以避免冲突。
        2. 将每个特殊符号替换为其对应的 '!x' 形式的编码。
    
    解码过程：
        1. 将所有 '!x' 形式的编码替换回原始符号。
        2. 将 ':E:' 替换回 '!'。
    
    Parameters
    ----------
    A : str or any type
        待处理的输入。如果不是字符串，会先转换为字符串。
    B : int, optional
        操作模式：
        - 1 (默认): 编码模式。将特殊符号转换为编码形式。
        - 其他值（通常为 0 或 2）: 解码模式。将编码形式还原为原始符号。
    
    Returns
    -------
    str
        编码或解码后的字符串。
        如果输入为空或 None，返回空字符串。
    
    Notes
    -----
    映射表（特殊符号 -> 编码）:
        ! -> !1     @ -> !2     # -> !3     $ -> !4     % -> !5
        ^ -> !6     & -> !7     * -> !8     ( -> !9     ) -> !0
        - -> !a     _ -> !b     = -> !c     + -> !d     ` -> !e
        ~ -> !f     [ -> !g     ] -> !h     { -> !i     } -> !j
        \\ -> !k    | -> !l     ; -> !m     : -> !n     ' -> !o
        " -> !p     , -> !q     . -> !r     < -> !s     > -> !t
        / -> !u     ? -> !v      (空格) -> !w     \t -> !x     \r -> !y     \n -> !z
    
    Examples
    --------
    >>> e36("Hello! World?")
    'Hello!nE!n!wWorld!v'
    
    >>> e36("Hello! World?", 1)
    'Hello!nE!n!wWorld!v'
    
    >>> e36("Hello!nE!n!wWorld!v", 2)
    'Hello! World?'
    
    >>> e36("Price: $100 & Tax=5%", 1)
    'Price!n!w!4100!w!7!wTax!c5!5'
    
    >>> e36("Price!n!w!4100!w!7!wTax!c5!5", 2)
    'Price: $100 & Tax=5%'
    """
    
    if not A:
        return ''
    
    A = str(A)

    a = '!@#$%^&*()-_=+`~[]{}\\|;:\'",.<>/? \t\r\n'
    b = '1234567890abcdefghijklmnopqrstuvwxyz'
    
    # 转为列表
    a = list(a)
    b = list(b)
    
    # 构建映射 c: c[a[z]] = '!'+b[z]
    c = {}
    for z in range(36):
        b[z] = '!' + b[z]  # 原地修改 b[z]
        c[a[z]] = b[z]
    
    l = len(a)

    if B == 1:
        # 编码: 先保护 '!'，再逐个替换
        A = A.replace('!', ':E:')
        for z in c:
            A = A.split(z)
            A = c[z].join(A)
        return A
    else:
        # 解码: 用映射表反向操作
        while True:
            for z in range(l):
                A = A.split(b[z]) 
                A = a[z].join(A)
            if A.find('!') < 0:  # 没有 '!' 了就跳出
                break
        A = A.replace(':E:', '!')
        return A

def b64(data: str, type: int = 1, rep: int = 1) -> str:
    '''
    对字符串进行 Base64 编码或解码，并可选是否进行字符替换（用于 URL 安全）。

    函数原型:
        b64(data: str, type: int = 1, rep: int = 1) -> str

    参数列表:
        data (str): 输入字符串
            - type=1: 待编码的明文（如 "hello+/"）
            - type=2: 待解码的 Base64 密文（如 "aGVsbG8rLw==" 或 "aGVsbG8tXw==")
            - type=3: 待转换格式的 Base64 字符串
        type (int): 操作类型：
            - 1: 编码（明文 → Base64，默认）
            - 2: 解码（Base64 → 明文）
            - 3: 仅格式转换（不做编解码）
        rep (int): 字符替换(replace)方式：
            - 1: 将 '+' 和 '/' 替换为 '-' 和 '_'（生成 URL 安全 Base64）
            - 2: 将 '-' 和 '_' 替换为 '+' 和 '/'（恢复标准 Base64）
            - 3: 不替换

    返回值:
        str: 处理后的字符串

    使用示例1: 编码为 URL 安全格式（推荐用于 Token、URL 参数）
        >>> b64("hello>?", type=1, rep=1)
        步骤1: 编码 → "aGVsbG8+Pzg="
        步骤2: 替换 '+'→'-', '/'→'_' → "aGVsbG8-Pzg="
        返回: "aGVsbG8-Pzg="

    使用示例2: 解码 URL 安全格式的 Base64
        >>> b64("aGVsbG8-Pzg=", type=2, rep=2)
        步骤1: 替换 '-'→'+', '_'→'/' → "aGVsbG8+Pzg="
        步骤2: 解码 → "hello>?"
        返回: "hello>?"

    使用示例3: 仅格式转换（不编解码）
        >>> b64("aGVsbG8+Pzg=", type=3, rep=1)
        将 '+'→'-', '/'→'_' → "aGVsbG8-Pzg="

        >>> b64("aGVsbG8-Pzg=", type=3, rep=2)
        将 '-'→'+', '_'→'/' → "aGVsbG8+Pzg="
        
    注意:
        - 编码时输入必须是字符串
        - 解码时输入必须是合法的 Base64 字符串，否则抛出异常
        - type 和 rep 必须为 1, 2, 3，否则抛出 ValueError
        - 该函数适用于生成 URL 安全的 Base64 字符串（如 JWT、Token）
    '''

    # 参数校验
    if type not in (1, 2, 3):
        raise ValueError("type 必须是 1(编码), 2(解码), 或 3(仅替换)")
    if rep not in (1, 2, 3):
        raise ValueError("rep 必须是 1(-_), 2(+/), 或 3(不替换)")

    # 统一处理流程
    result = data
    type = int(type)
    rep = int(rep)

    # 步骤1：根据 type 执行编码/解码
    if type == 1:
        # 编码：str → bytes → b64 → str
        data_bytes = data.encode('utf-8')
        b64_bytes = base64.b64encode(data_bytes)
        result = b64_bytes.decode('ascii')  # 得到标准 Base64 字符串
        # 如果 replace=1，替换为 URL 安全格式
        if rep == 1:
            result = result.replace('+', '-').replace('/', '_')

    elif type == 2:
        # 解码：必须先恢复标准 Base64 格式
        result = result.replace('-', '+').replace('_', '/')
        # 确保填充正确
        missing_padding = len(result) % 4
        if missing_padding:
            result += '=' * (4 - missing_padding)
        try:
            b64_bytes = result.encode('ascii')
            decoded_bytes = base64.b64decode(b64_bytes)
            result = decoded_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Base64 解码失败，请检查输入是否为合法 Base64 字符串: {e}")

    elif type == 3:
        # 仅格式转换，不编解码
        if rep == 1:
            result = result.replace('+', '-').replace('/', '_')
        elif rep == 2:
            result = result.replace('-', '+').replace('_', '/')

    return result

def md5(data: str, encoding: str = 'utf-8') -> str:
    '''
    计算字符串的 MD5 哈希值。

    函数原型:
        md5(data: str, encoding: str = 'utf-8') -> str

    参数列表:
        data (str): 要计算哈希的输入字符串（支持中文）
        encoding (str): 字符串编码方式，默认为 'utf-8'

    返回值:
        str: 32位小写 MD5 哈希值（十六进制字符串）

    使用示例1:
        >>> md5("hello")
        '5d41402abc4b2a76b9719d911017c592'

    使用示例2:
        >>> md5("你好世界")
        '6f1ed002ab5595859014ebf0951522d9'

    使用示例3:
        >>> md5("password", encoding="gbk")
        'e10adc3949ba59abbe56e057f20f883e'

    注意:
        - 输入必须是字符串类型
        - 推荐使用 UTF-8 编码处理中文
        - MD5 不是加密算法，仅用于校验或简单哈希，不推荐用于安全敏感场景
    '''

    if not isinstance(data, str):
        raise TypeError("data 必须是字符串类型")

    # 将字符串按指定编码转换为字节
    try:
        data_bytes = data.encode(encoding)
    except LookupError:
        raise ValueError(f"不支持的编码格式: {encoding}")

    # 计算 MD5
    hash_obj = hashlib.md5(data_bytes)
    return hash_obj.hexdigest()  # 返回32位小写十六进制字符串

def md5_file(path: str) -> str:
    '''
    计算指定文件的 MD5 哈希值。

    函数原型:
        md5_file(path: str) -> str

    参数列表:
        path (str): 文件路径（必须存在且为普通文件）

    返回值:
        str: 32位小写 MD5 哈希值（十六进制字符串），如果文件不存在或不是文件则返回 None

    使用示例1:
        >>> md5_file("example.txt")
        'd41d8cd98f00b204e9800998ecf8427e'

    使用示例2:
        >>> md5_file("/path/to/image.jpg")
        'a1b2c3d4e5f6...'

    注意:
        - 支持任意大小的文件（逐块读取，不占内存）
        - 使用 8192 字节块大小，性能良好
        - 如果文件不存在或权限不足，会抛出异常
    '''

    if not os.path.exists(path):
        raise FileNotFoundError(f"文件不存在: {path}")

    if not os.path.isfile(path):
        raise ValueError(f"路径不是文件: {path}")

    hash_md5 = hashlib.md5()
    chunk_size = 8192  # 8KB 每块，平衡性能与内存

    try:
        with open(path, 'rb') as f:  # 必须以二进制模式读取
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
    except PermissionError:
        raise PermissionError(f"无权限读取文件: {path}")
    except Exception as e:
        raise RuntimeError(f"读取文件时发生错误: {e}")

    return hash_md5.hexdigest()  # 返回32位小写十六进制字符串

def sha(data='', type=2):
    '''
    计算字符串的 SHA 哈希值（摘要）。

    支持 SHA-1、SHA-256、SHA-512 等算法。
    输入自动转为 UTF-8 字节，输出为小写十六进制字符串。

    参数:
        data (str): 要计算哈希的字符串（支持任意 Unicode 字符）
        type (int): 哈希算法类型：
                    1 -> SHA-1   (160位, 输出40字符)
                    2 -> SHA-256 (256位, 输出64字符, 默认)
                    3 -> SHA-512 (512位, 输出128字符)

    返回:
        str: 对应算法的十六进制小写哈希字符串

    异常:
        ValueError: 当 type 不支持时抛出

    使用示例:

    示例1: 默认使用 SHA-256
        >>> sha("hello")
        '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'

    示例2: 使用 SHA-1
        >>> sha("hello", type=1)
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'

    示例3: 使用 SHA-512
        >>> sha("hello", type=3)
        '9b71d224bd62f3785d9699bf900ef823d46b7e426d21dc2f83a71f6a939a835e51156827af82678d62558e277b82f78a1e748923c158880d3a69a36482790522'

    示例4: 中文字符串
        >>> sha("你好世界")
        '606ec6e9903a641a396c0c86539155825efc7edf07321d9ce08d76eb19f1505e'

    示例5: 空字符串
        >>> sha("")
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

    注意:
        - 推荐使用 SHA-256 或 SHA-512，SHA-1 已不安全。
        - 所有输入均按 UTF-8 编码处理。
        - 输出为小写十六进制字符串，不可逆。
    '''

    # 参数验证
    if not isinstance(data, str):
        raise TypeError("data must be a string")

    # 转为 UTF-8 字节
    data_bytes = data.encode('utf-8')
    type = int(type)

    # 根据 type 选择算法
    if type == 1:
        hash_obj = hashlib.sha1(data_bytes)
        return hash_obj.hexdigest()

    elif type == 2:
        hash_obj = hashlib.sha256(data_bytes)
        return hash_obj.hexdigest()

    elif type == 3:
        hash_obj = hashlib.sha512(data_bytes)
        return hash_obj.hexdigest()

    else:
        raise ValueError(f"Unsupported hash type: {type}. Use 1, 2, or 3.")
    

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
    parser.add_argument('-f', '--func', action='store_true')
    parser.add_argument('-h', '--func_help', default='')
    parser.add_argument('-r', '--run')
    parser.add_argument('-p', '--para', default='')

    args = parser.parse_args(args)
    
    if args.version:
        print(VER)
    elif args.copr:
        print(COPR)
    elif args.info:
        print(INFO)
    elif args.help:
        print(HELP)

    # 显示所有函数
    elif args.func:
        # mod = _load(f"{__package__}.{mname}")
        mod = sys.modules[__name__]
        funcs = _get_functions(mod)
        print(f'\n可以在参数(-h)后加函数名称查看该函数的帮助信息，如：rypi comm -h b64。')
        print(f'\n运行函数时输入的参数值可使用列表或字典两种模式，如：')
        print(f'\n列表模式：rypi comm -r sha -p "abcdef 2"')
        print(f'\n字典模式：rypi comm -r sha -p "data=abcdef type=2"')
        print(f'\n如果参数值有空格需要加引号，如：')
        print(f'\n列表模式：rypi comm -r sha -p "\'abc def\' 3"')
        print(f'\n字典模式：rypi comm -r sha -p "data=\'abc def\' type=3"')
        print(f'\nfunction list:')
        for name, desc in funcs:
            print(f'\n    {name}: {desc}')

    # 显示指定函数的帮助信息
    elif args.func_help:
        # mod = sys.modules[__name__]
        # func = getattr(mod, args.func_help, None)
        func = globals().get(args.func_help)
        if not func or not inspect.isfunction(func):
            print(f'函数 {args.run} 不存在或不是函数')
            return
        doc = inspect.getdoc(func) or '无描述'
        print(f'\n{doc}')

    # 运行指定函数
    elif args.run:
        # mod = sys.modules[__name__]
        # func = getattr(mod, args.run, None)
        func = globals().get(args.run)
        if not func or not inspect.isfunction(func):
            print(f'函数 {args.run} 不存在或不是函数')
            return

        # 解析参数
        plist = _parse_args(args.para)
        print(f'\n运行: {args.run}({plist})')
        if isinstance(plist, list):
            res = func(*plist)
        elif isinstance(plist, dict):
            res = func(**plist)
        else:
            raise TypeError(f"不支持的参数类型: {type(plist)}")
        print(f'\n运行结果: {res}')

    # 显示帮助
    else:
        print(HELP)

if __name__ == '__main__':
    main()
