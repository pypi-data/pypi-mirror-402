#!/usr/bin/env python
'''
应用接口
'''

def fobj(obj, indent=4):
    '''format obj'''
    import json
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(json.dumps(obj, indent=indent, ensure_ascii=False, default=str))

def api(data):
    return data