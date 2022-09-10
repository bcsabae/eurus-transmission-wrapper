from transmission_rpc import Client
from transmission_rpc import Torrent
from transmission_rpc.torrent import Status
from urllib.parse import urlparse

class WrappedClient():
    _client = None

    def __init__(self, url, username=None, password=None) -> None:
        self._url = url
        self._username = username
        self._password = password
        parsed_url = urlparse(url)
        self._client = Client(host=parsed_url.hostname, port=parsed_url.port, path=parsed_url.path, username=username, password=password)
        return

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

    def get_torrents(self) -> list:
        torrents = self._client.get_torrents()
        torrents_mapped = []
        for torrent in torrents:
            torrents_mapped.append(self.torrent_map(torrent))
        return torrents_mapped

    def get_torrent(self, id: int) -> dict:
        torrent = self._client.get_torrent(id)
        return self.torrent_map(torrent)