from crypt import methods
from email import header
import json
from textwrap import wrap
from typing import Any
from flask import Flask
from flask import request
from flask import Response
from flask import make_response
from WrappedClient import WrappedClient
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
client = WrappedClient(username="transmission", password="transmission")
debug_origin = '*'

def response(status: str, data: Any=None) -> str:
    response_json = {
        'status': status,
        'data': data if data != None else {}
    }
    resp = Response(response=json.dumps(response_json))
    resp.headers['Access-Control-Allow-Origin'] = debug_origin
    resp.content_type = 'application/json'
    return resp

def online(func) -> Any:
    def wrapper(*args, **kwargs) -> Any:
        if not client.is_connected():
            return response('not connected')
        if not client.is_authenticated():
            return response("not authenticated")
        return func(*args, **kwargs)
    return wrapper

def connected(func) -> Any:
    def wrapper(*args, **kwargs) -> Any:
        if not client.is_connected():
            return response('not connected')
        return func(*args, **kwargs)
    return wrapper

def validate_id(func) -> Any:
    def wrapper(*args, **kwargs) -> Any:
        if 'id' in kwargs:
            id = kwargs['id']
        else:
            id = args[0]
        try:
            id_int = int(id)
            if id_int < 0:
                raise ValueError
        except ValueError:
            return response('invalid id format')
        return func(*args, **kwargs)
    return wrapper

@app.get('/status', endpoint='status')
@online
def status():    
    return response("success")

@app.get('/torrents', endpoint='get_torrents')
@online
def get_torrents():
    torrents = client.get_torrents()
    if torrents != None:
        return response('success', torrents)
    else:
        return response('request error')

@app.get('/torrents/<id>', endpoint='get_torrent')
@online
@validate_id
def get_torrent(id=id):  
    torrent = client.get_torrent(int(id))
    if torrent == None:
        return response('not found')
    return response('success', torrent)

@app.get('/torrents/<id>/stop', endpoint='stop_torrent')
@online
@validate_id
def stop_torrent(id=id):
    torrent = client.stop_torrent(int(id))
    if torrent == None:
        return response('not found')
    return response('success', torrent)

@app.get('/torrents/<id>/start', endpoint='start_torrent')
@online
@validate_id
def stop_torrent(id=id):
    torrent = client.start_torrent(int(id))
    if torrent == None:
        return response('not found')
    return response('success', torrent)

@app.get('/torrents/<id>/delete', endpoint='delete_torrent')
@online
@validate_id
def delete_torrent(id=id):
    resp = client.delete_torrent(int(id))
    if resp == None:
        return response('not found')
    else:
        return response('success')

@app.get('/config', endpoint='get_config')
def get_config():
    config = client.get_config()
    return response('success', config)

@app.post('/config', endpoint='set_config')
def set_config():
    missing_key = False
    requested_config = request.get_json(force=True)
    for key in requested_config:
        print(f'reuqesting to change {key}')
        if client.set_config(key, requested_config[key]) == None:
            missing_key = True
    
    if missing_key:
        return response('missing key', client.get_config())
    else:
        return response('success', client.get_config())