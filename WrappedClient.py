from ctypes import Union
from typing import Callable, Dict
from transmission_rpc import Client, Torrent
from transmission_rpc.torrent import Status
import transmission_rpc.error as error
from urllib.parse import urlparse
import json
import logging

class WrappedClient:
    """ Wrapper class for transmission_rpc's RPC client.

    Public attributes: None


    Public functions:

        Constructor:
            __init__(self, username: str = None, password: str = None, config_file: str = 'config.json') -> None: Class constructor


        Static methods:
            status_map(status: Status) -> int: Maps transmission_rpc statuses back to RPC status numbers.
            torrent_map(torrent: Torrent) -> Dict: Maps a Torrent object to RPC style dictionary.


        Decorators:
            connection_needed(func: Callable) -> Union[Callable, None]: Wrapper to make sure the client has active connection to the RPC server. 
                If not, an error is reported and None is returned.


        connect(self) -> bool: Connect to RPC server.

        get_config(self, key: str = None) -> Union[Dict, str, None]: Get configuration. Based on the passed key, return the whole 
            configuration dictionary or a specific value.
        set_config(self, key: str, value: str) -> Union[str, bool, None]: Set configuration. This function also writes the config to a file.
            If the requested change is the RPC server address, also initate reconnection.
        is_connected(self) -> bool: If the client is connected to the RPC server
        is_authenticated(self) -> bool: If the client is authenticated with the RPC server.
        get_torrents(self) -> list: Get torrents from RPC server
        get_torrent(self, id: int) -> Union[dict, None]: Get a specific torrent.
        start_torrent(self, id: int) -> Union[dict, None]: Start a torrent.
        stop_torrent(self, id: int) -> Union[dict, None]: Stop a torrent.
        add_torrent(self, filename: str, location: str) -> Union[str, None]: Add torrent.
        delete_torrent(self, id: int) -> Union[int, None]: Delete a torrent.

    
    Raises:
        FileNotFoundError: if config file provided in the constructor doesn't exist
    """

    # Class properties

    _client = None
    _config = None
    _config_file = None
    _connected = None
    _authenticated = None


    # Constructor

    def __init__(self, username: str = None, password: str = None, config_file: str = 'config.json') -> None:
        """ Class constructor.

        Args:
            username (str, optional): Username to use with RPC server. Defaults to None.
            password (str, optional): Password to use with RPC server. Defaults to None.
            config_file (str, optional): Configuration file name. Defaults to 'config.json'.

        Raises:
            FileNotFoundError: Raised if the provided configuration file couldn't be found
        """
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


    # Static methods

    @staticmethod
    def status_map(status: Status) -> int:
        """ Maps transmission_rpc statuses back to RPC status numbers.

        Args:
            status (Status): transmission_rpc status

        Returns:
            int: status number in RPC convention
        """
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
    def torrent_map(torrent: Torrent) -> Dict:
        """ Maps a Torrent object to RPC style dictionary.

        Args:
            torrent (Torrent): Torrent to map

        Returns:
            Dict: RPC-style mapped JSON object
        """
        torrent_dict = {}
        torrent_dict['id'] = torrent.id
        torrent_dict['name'] = torrent.name
        torrent_dict['status'] = WrappedClient.status_map(torrent.status)
        torrent_dict['percentDone'] = torrent.progress
        torrent_dict['sizeWhenDone'] = torrent.size_when_done
        torrent_dict['rateDownload'] = torrent.rateDownload
        torrent_dict['downloadDir'] = torrent.download_dir
        return torrent_dict


    # Decorators
    def connection_needed(func: Callable) -> Union[Callable, None]:
        """ Wrapper to make sure the client has active connection to the RPC server. If not, an error is reported and None is returned.

        Args:
            func (Callable): Function for the decorator

        Returns:
            Union[Callable, None]: Return the function or None on error.
        """
        def wrapper(*args, **kwargs) -> Callable:
            # check connection
            if args[0].is_connected():
                return func(*args, **kwargs)
            else:
                logging.error("Function call prevented, client is not connected")
                return None
        return wrapper


    # Private functions

    def _write_config(self) -> bool:
        """ Write configuration to confir file.

        Returns:
            bool: if the write was successful
        """
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


    # Public functions

    def connect(self) -> bool:
        """ Connect to RPC server.

        Returns:
            bool: if the connection was successful
        """
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


    def get_config(self, key: str = None) -> Union[Dict, str, None]:
        """ Get configuration. Based on the passed key, return the whole configuration dictionary or a specific value.

        Args:
            key (str, optional): Requested configuration value's key. If None used, return whole configuration. Defaults to None.

        Returns:
            Union[Dict, str, None]: On success, return the value, or the whole configuration. If a non-existing key was requested, 
            return None.
        """
        if key == None:
            return self._config
        try:
            value = self._config[key]
        except KeyError:
            logging.debug(f"Tried to access non-existing config: {key}")
            value = None
        return value


    def set_config(self, key: str, value: str) -> Union[str, bool, None]:
        """ Set configuration. This function also writes the config to a file. If the requested change is the RPC server address,
        also initate reconnection.

        Args:
            key (str): Configuration to set.
            value (str): Value to set the configuration to.

        Returns:
            Union[str, bool, None]: The requested config value on success, False on writing error.
        """
        if key not in self._config:
            return None
        self._config[key] = value
        could_write = self._write_config()
        if key == "server_address":
            logging.info(f"Server address modified, reconnecting to {self._config[key]}")
            self.connect()
        
        return value if could_write else False


    def is_connected(self) -> bool:
        """ If the client is connected to the RPC server

        Returns:
            bool: indicating connection status
        """
        return self._connected if self._connected != None else False
    

    def is_authenticated(self) -> bool:
        """ If the client is authenticated with the RPC server.

        Returns:
            bool: indicating authentication status
        """
        return self._authenticated if self._authenticated != None else False


    @connection_needed
    def get_torrents(self) -> list:
        """ Get torrents from RPC server

        Returns:
            list: torrents
        """
        torrents = self._client.get_torrents()
        torrents_mapped = []
        for torrent in torrents:
            torrents_mapped.append(self.torrent_map(torrent))
        return torrents_mapped


    @connection_needed
    def get_torrent(self, id: int) -> Union[dict, None]:
        """ Get a specific torrent.

        Args:
            id (int): ID of the torrent to get

        Returns:
            Union[dict, None]: The torrent in RPC JSON format on succes, None if there was no torrent with the given ID
        """
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        return self.torrent_map(torrent)


    @connection_needed
    def start_torrent(self, id: int) -> Union[dict, None]:
        """ Start a torrent.

        Args:
            id (int): ID of the torrent

        Returns:
            Union[dict, None]: The torrent in RPC JSON format on succes, None if there was no torrent with the given ID
        """
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        torrent.start()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)


    @connection_needed
    def stop_torrent(self, id: int) -> Union[dict, None]:
        """ Stop a torrent.

        Args:
            id (int): ID of the torrent

        Returns:
            Union[dict, None]: The torrent in RPC JSON format on succes, None if there was no torrent with the given ID
        """
        try:
            torrent = self._client.get_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        torrent.stop()
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)
    

    @connection_needed
    def add_torrent(self, filename: str, location: str) -> Union[str, None]:
        """ Add torrent.

        Args:
            filename (str): name of the .torrent file
            location (str): download location on the RPC server as an absolute path

        Returns:
            Union[str, None]: RPC server's response on success, None on RPC server or file error
        """
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


    @connection_needed
    def delete_torrent(self, id: int) -> Union[int, None]:
        """ Delete a torrent.

        Args:
            id (int): ID of the torrent

        Returns:
            Union[int, None]: id of the deleted torrent on success, None if torrent with the given ID was not found
        """
        try:
            self._client.remove_torrent(id)
        except KeyError:
            logging.debug(f"No torrent with ID {id}")
            return None
        return id
