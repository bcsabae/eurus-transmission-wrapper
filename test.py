from WrappedClient import WrappedClient

client = WrappedClient(username="transmission", password="transmission")
print(client.get_torrents())
client.delete_torrent(2)
