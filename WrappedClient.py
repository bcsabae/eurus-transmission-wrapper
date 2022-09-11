from typing import Any
from transmission_rpc import Client
from transmission_rpc import Torrent
from transmission_rpc.torrent import Status
import transmission_rpc.error as error
from urllib.parse import urlparse
import json

class WrappedClient():
    _client = None
    _config = None
    _config_file = None
    _connected = None
    _authenticated = None

    def __init__(self, username=None, password=None, config_file='config.json') -> None:
        self._config_file = config_file
        self._username = username
        self._password = password

        # TODO: check if config file is writeable
        try:
            with open(self._config_file) as cf:
                self._config = json.load(cf)
        except FileNotFoundError:
            # LOG: config file not found
            print("file not found")
            return

        self.connect()
        
        return

    def connect(self) -> bool:
        self._url = self.get_config('server_address')
        if self._url == None:
            # LOG: not a valid URL
            print("not a valid URL")
            self._connected = False
            return False

        parsed_url = urlparse(self._url)
        if parsed_url.scheme != 'http' or not parsed_url.netloc:
            # LOG
            print("not a valid url")
            self._connected = False
            return False

        try:
            self._client = Client(host=parsed_url.hostname, port=parsed_url.port, path=parsed_url.path, username=self._username, password=self._password)
            self._connected = True
            self._authenticated = True
            return True
        except error.TransmissionConnectError:
            # LOG: cannot connect to server
            print("cannot connect to server")
            self._connected = False
            return False
        except error.TransmissionAuthError:
            # LOG: authentication failure
            print("authentication failure")
            self._connected = True
            self._authenticated = False
            return False
        return False

    def connection_needed(func) -> Any:
        def wrapper(*args, **kwargs) -> Any:
            # check connection
            if args[0].is_connected():
                return func(*args, **kwargs)
            else:
                print("not connected")
                return None
        return wrapper

    def _write_config(self) -> bool:
        try:
            with open(self._config_file, 'w') as cf:
                json.dump(self._config, cf)
        except FileNotFoundError:
            return False
        except PermissionError:
            return False
        return True

    def get_config(self, key: str = None) -> Any:
        if key == None:
            print(self._config)
            return self._config
        try:
            value = self._config[key]
        except KeyError:
            value = None
        return value

    def set_config(self, key: str, value: str) -> Any:
        if key not in self._config:
            return None
        self._config[key] = value
        could_write = self._write_config()
        if key == "server_address":
            self.connect()
        
        return value if could_write else False

    def is_connected(self) -> bool:
        return self._connected if self._connected != None else False
    
    def is_authenticated(self) -> bool:
        return self._authenticated if self._authenticated != None else False


    @staticmethod
    def status_map(status: Status) -> int:
        if status.stopped:
            return 0
        elif status.check_pending:
            return 1
        elif status.checking:
            return 2
        elif status.download_pending:
            return 3
        elif status.downloading:
            return 4
        elif status.seed_pending:
            return 5
        elif status.seeding:
            return 6

    @staticmethod
    def torrent_map(torrent: Torrent) -> str:
        torrent_dict = {}
        torrent_dict['id'] = torrent.id
        torrent_dict['name'] = torrent.name
        torrent_dict['status'] = WrappedClient.status_map(torrent.status)
        torrent_dict['percentDone'] = torrent.progress
        torrent_dict['sizeWhenDone'] = torrent.size_when_done
        torrent_dict['rateDownload'] = torrent.rateDownload
        torrent_dict['downloadDir'] = torrent.download_dir
        return torrent_dict

    @connection_needed
    def get_torrents(self) -> list:
        torrents = self._client.get_torrents()
        torrents_mapped = []
        for torrent in torrents:
            torrents_mapped.append(self.torrent_map(torrent))
        return torrents_mapped

    @connection_needed
    def get_torrent(self, id: int) -> dict:
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            return None
        return self.torrent_map(torrent)

    @connection_needed
    def stop_torrent(self, id: int) -> dict:
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            return None
        torrent.stop()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)

    @connection_needed
    def start_torrent(self, id: int) -> dict:
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            return None
        torrent.start()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)

    @connection_needed
    def delete_torrent(self, id: int) -> Any:
        try:
            resp = self._client.remove_torrent(id)
        except KeyError:
            return None
        return id
