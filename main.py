import json
from textwrap import wrap
from typing import Any
from flask import Flask
from flask import request
from flask import Response
from WrappedClient import WrappedClient
import json
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from logging.config import dictConfig
import logging


# App configuration
UPLOAD_FOLDER = './tmp'
LOG_FILE = './log/app.log'

# Logging configuration
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s\t\t in %(funcName)s\t of %(module)s\t: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'detailed'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

# Instantiate app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Remove this if you don't need CORS
CORS(app)
debug_origin = '*'

# Instantiate wrapper
client = WrappedClient()



# API functions

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
def start_torrent(id=id):
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

@app.post('/torrents/new', endpoint='add_torrent')
@online
def add_torrent():
    if request.method == "POST":
        if 'path' not in request.form:
            logging.info("No download location provided")
            return response('no location')
        
        if 'file' not in request.files:
            logging.info('No file was sent in request')
            return response('no file')
        file = request.files['file']
        if file.filename == '':
            logging.info("Empty file sent in request")
            return response('no file')
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'torrent'):
            logging.info(f"Bad file format: {file.filename}")
            return response('bad file format')
        filename = secure_filename(file.filename)
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(full_filename)
        
        download_path = request.form['path']
        
        resp = client.add_torrent(full_filename, download_path)
        os.remove(full_filename)
        
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
        logging.info(f"Requesting change for config {key} to {requested_config[key]}")
        if client.set_config(key, requested_config[key]) == None:
            missing_key = True
    
    if missing_key:
        return response('missing key', client.get_config())
    else:
        return response('success', client.get_config())