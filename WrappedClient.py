from typing import Any
from transmission_rpc import Client
from transmission_rpc import Torrent
from transmission_rpc.torrent import Status
import transmission_rpc.error as error
from urllib.parse import urlparse
import json
import logging

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

        logging.info("App started")

        try:
            with open(self._config_file) as cf:
                self._config = json.load(cf)
        except FileNotFoundError:
            logging.critical(f"Config file not found: {self._config_file}")
            raise FileNotFoundError

        self.connect()
        
        return

    def connect(self) -> bool:
        self._url = self.get_config('server_address')
        logging.info(f"Connecting to {self._url}")
        if self._url == None:
            logging.error(f"{self._url} is not a valid URL, aborting connection")
            self._connected = False
            return False

        parsed_url = urlparse(self._url)
        if parsed_url.scheme != 'http' or not parsed_url.netloc:
            logging.error(f"{self._url} is not a valid URL, aborting connection")
            self._connected = False
            return False

        try:
            self._client = Client(host=parsed_url.hostname, port=parsed_url.port, path=parsed_url.path, username=self._username, password=self._password)
            self._connected = True
            self._authenticated = True
            return True
        except error.TransmissionConnectError:
            logging.error(f"Cannot connect to RPC server at {self._url}")
            self._connected = False
            return False
        except error.TransmissionAuthError:
            logging.error("Authentication failre, aborting connection")
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
                logging.debug("Function call prevented, client is not connected")
                return None
        return wrapper

    def _write_config(self) -> bool:
        try:
            with open(self._config_file, 'w') as cf:
                json.dump(self._config, cf)
        except FileNotFoundError:
            logging.error(f"Cannot write config: {self._config_file} not found")
            return False
        except PermissionError:
            logging.error(f"Cannot write config: {self._config_file} is not writeable")
            return False
        return True

    def get_config(self, key: str = None) -> Any:
        if key == None:
            return self._config
        try:
            value = self._config[key]
        except KeyError:
            logging.debug(f"Tried to access non-existing config: {key}")
            value = None
        return value

    def set_config(self, key: str, value: str) -> Any:
        if key not in self._config:
            return None
        self._config[key] = value
        could_write = self._write_config()
        if key == "server_address":
            logging.info(f"Server address modified, reconnecting to {self._config[key]}")
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
            logging.debug(f"No torrent with ID {id}")
            return None
        return self.torrent_map(torrent)

    @connection_needed
    def stop_torrent(self, id: int) -> dict:
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        torrent.stop()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)

    @connection_needed
    def start_torrent(self, id: int) -> dict:
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        torrent.start()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)

    @connection_needed
    def delete_torrent(self, id: int) -> Any:
        try:
            resp = self._client.remove_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        return id
    
    @connection_needed
    def add_torrent(self, filename, location):
        try:
            with open(filename, 'rb') as file:
                try:
                    resp = self._client.add_torrent(file, download_dir=location)
                except error.TransmissionError as e:
                    logging.debug(f"API error: {e.message}")
                    return None
                except TypeError:
                    logging.debug("Invalid file")
                    return None
                return resp
        except FileNotFoundError:
            logging.debug(f"File {filename} doesn't exist")
            return None
        return None
