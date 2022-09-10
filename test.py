from WrappedClient import WrappedClient

client = WrappedClient("http://192.168.2.100:9091/transmission/rpc", username="transmission", password="transmission")
print(client.get_torrents())
