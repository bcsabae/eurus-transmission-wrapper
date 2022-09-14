# Eurus Transmission Wrapper API

Eurus Transmission Wrapper API is a very simplistic wrapper for the [transmission_rpc](https://github.com/Trim21/transmission-rpc/) Python library. The reason why this project was born is that while the [RPC API](https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md) provides a very detailed way on how to communicate with a Transmission server, it's a complex specification with features that people don't need for everyday torrenting. This wrapper exposes few of the everyday functions an average user would need:
- viewing torrents
- (re)start a torrent
- stop a torrent
- add new torrent
- delete existing torrent

The project includes a Flask server that serves the API itself. The API is designed in a way that it's naming convention is the same as in the RPC specifications, to provide cross-project compatibility. A detailed API specification of this project can be found in `doc/API-SPEC.md`.

## Structure

The main server file, `main.py` needs to be ran by Flask. It will initiate a `WrappedClient` class, which contains logic to communicate with the RPC server, using the `transmission_rpc` library in its internals. The class is fully documented in docstrings.

### Configuration

The behavior of the client can be modified from a `config.json` file. You can use a different config file by setting the environment variable `EURUS_WRAPPER_CONFIG` as the config path file and location. A default `config.json.example` is provided.

Configurable parameters are:
- `server_address`: address of the RPC server to connect to
- `default_download_dir`: default download location to request from RPC server

Configurations are exposed through the API (see the specification), and thus can change from within the application.

### Authentication

Authentication towards the RPC server is supported in two ways:
- directly through source code (modifying the constructor call in the Flask server)
- through environment varialbes, setting `EURUS_WRAPPER_RPC_USERNAME` and `EURUS_WRAPPER_RPC_PASSWORD`

## Licensing and disclaimer

**Disclaimer:** This project was made for own use and is not extensively tested. Use at your own risk. Don't use this software for anything illegal, I'm not responsible for that!

This project runs under GNU General Public License v3.