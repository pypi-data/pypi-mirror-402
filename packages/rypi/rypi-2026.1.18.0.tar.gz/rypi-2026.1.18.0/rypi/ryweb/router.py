
#!/usr/bin/env python
'''
网站路由器
'''

import os
import sys
import importlib.util
import json
from fastapi import FastAPI, Request
from rypi import comm

app = FastAPI()

def fobj(obj, indent=4):
    '''format obj'''
    import json
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(json.dumps(obj, indent=indent, ensure_ascii=False, default=str))

# 处理原始请求对象
@app.api_route('/{path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
async def request_info(req: Request):
    query = {}
    obj = {}
    body = ''
    query = dict(req.query_params)
    head = dict(req.headers)

    # 根据 Content-Type 处理不同类型的数据
    ct = req.headers.get('content-type', '').lower()

    try:
        if 'application/json' in ct:
            # JSON 数据
            try:
                obj = await req.json()
            except json.JSONDecodeError as e:
                d = (await req.body()).decode('utf-8')
                obj = comm.obj(comm.e36(d, 0))
        elif 'application/x-www-form-urlencoded' in ct:
            # 表单数据
            d0 = await req.body()
            d = await req.form()
            if d:
                obj = {k: v for k, v in d.items()}
            else:
                d = (await req.body()).decode('utf-8')
                obj = comm.obj(comm.e36(d, 0))
        elif 'multipart/form-data' in ct:
            # 多部分表单（包含文件上传）
            d = await req.form()
            for k, v in d.items():
                if hasattr(v, 'filename'):
                    ctt = await v.read()
                    obj['ctt'] = ctt
                    obj['name'] = v.filename
                    obj['type'] = v.content_type
                    obj['size'] = len(ctt)
                else:
                    obj[k] = comm.e36(v, 0)
        else:
            # 其他类型，获取原始数据
            body = (await req.body()).decode('utf-8')
            body = comm.obj(comm.e36(body, 0))
    except Exception as e:
        body = f"Parse Error: {str(e)}"

    if 'x-forwarded-for' in req.headers:
        # 如果有代理，取第一个IP
        cip = req.headers['x-forwarded-for'].split(',')[0]
    elif 'x-real-ip' in req.headers:
        cip = req.headers.get('x-real-ip')
    else:
        cip = req.client.host if req.client else '0.0.0.0'

    core = {
        'cdir': head.get('x-code-dir', '').lower(),
        'wdir': head.get('x-web-dir', '').lower(),
        'hname': head.get('x-host-name', '').lower(),
        'meth': req.method,
        'url': str(req.url),
        'ref': head.get('referer'),
        'ori': head.get('origin'),
        'host': head.get('host').lower(),
        'ua': head.get('user-agent'),
        'cip': cip
    }

    data = {}
    data['HEAD'] = head
    data['CORE'] = core
    objs = [query, obj]
    if isinstance(body, dict):
        objs.append(body)
    for o in objs:
        for k, v in o.items():
            data[k] = v

    path = f'{core.get("cdir")}/{core.get("hname")}/app.py'
    spec = None
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location("app", path)
    if spec is not None:
        app = importlib.util.module_from_spec(spec)
        sys.modules["app"] = app
        spec.loader.exec_module(app)
    else:
        from rypi.ryo import app

    # 检查模块是否有指定函数（存在且可调用）
    isapi = hasattr(app, 'api') and callable(app.api)
    if isapi:
        res = app.api(data)
    else:
        res = {'errno': 1, 'errmsg': '入口模块加载错误'}
    return fobj(res)
