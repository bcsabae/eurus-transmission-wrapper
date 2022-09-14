# Eurus transmission UI

Eurus is a lightweight user interface implementing some very basic features of Transmission RPC. The idea in mind is to have a **very** simple UI with **minimal** features in a modern SPA application. Because the way Transmission RPC is architectured, and some complications with its implementation by the Transmission daemon (e.g. not supporting OPTIONS requests and thus making cross-origin requests possible only with a proxy), a supplemental server is also included with the project. This has the RPC implementation itself, and exposes the needed (minimal) services through a much simpler and SPA-styled API. This design simplifies some part, while adds more complexity to others, but adding this one additional layer also opens the opportunity to expand Transmission's features while leaving the daemon itself unchanged.

## API specification

The API has to provide the following to the application:

- Torrent getters, including some of their parameters (status, progress, speed, etc)
- Torrent setters, restricted to adding, removing, and pausing torrents
- Application settings like server URL

A response has the following structure:

```
{
    'status': <response status>,
    'data': <response data>
}
```

`status` can be one of the following values:
- `success`: request was successful
- `request error`: RPC request failed
- `not connected`: couldn't connect to RPC server
- `not authenticated`: RPC server authentication failed
- `invalid id format`: id format of torrent was invalid
- `not found`: requested torrent is not found
- `no location`: no `location` parameter was provided with a new torrent request
- `no file`: no file was provided with a new torrent request 
- `bad file format`: file provided with a new torrent request has bad format
- `missing key`: a configuration modification was requested, but the provided key doesn't match any configuration value

`data` can be any valid JSON object, as well as a JSON array. In case `status` is not showing success, this field *may* contain an error message, but it may not be present at all.

### Torrent accessors

#### Get all torrents

Get all torrents stored by the torrent client.

##### Request

|Request endpoint | Request type | Request parameters |
| --------------- | ------------ | ------------------ |
| /torrents       | GET          | none               |

##### Response:

Possible `status` values: `success`, `request error`, `not connected`, `not authenticated`

Array containing all torrents with the following format:

```
{
    'status': 'success',
    'data': [{
        'id': 123456,
        'name': 'An.Example.Torrent',
        'status': 5 
        'percentDone': 0.42,
        'sizeWhenDone': 1413451432,
        'rateDownload': 3715519,
        'downloadDir': '/opt/transmission-daemon/torrents/download'   
    },

    // possibly more objects
    // ...

    ]
```

The keys and values are equivalent to those defined in the RPC specification. They are:

- `id`: UID of the torrent in the server
- `name`: name of the torrent file
- `status`: status integer, described below
- `percentDone`: how much has been downloaded from the files
- `sizeWhenDone`: byte count of all the data that we'll have once the download is finished
- `rateDownload`: N/A
- `downloadDir`: download path for torrent

The status values reported by `status` are the following:

- 0: stopped
- 1: queued to verify local data
- 2: verifying local data
- 3: queued to download
- 4: downloading
- 5: queued to seed
- 6: seeding

#### Get specific torrent

Get a specific torrent from the torrent client.

##### Request

|Request endpoint | Request type | Request parameters |
| --------------- | ------------ | ------------------ |
| /torrents/{id}  | GET          | `id`: torrent ID   |

##### Response

Possible `status` values: `success`, `not found`, `not connected`, `not authenticated`

The specific requested torrent, or an error response.

```
{
    'status': 'success',
    'data': {
        'id': 123456,
        'name': 'An.Example.Torrent',
        'status': 5 
        'percentDone': 0.42,
        'sizeWhenDone': 1413451432,
        'rateDownload': 3715519,
        'downloadDir': '/opt/transmission-daemon/torrents/download',    
    }
}
```

### Torrent modifiers

#### Stop torrent

Stop specific torrent.

##### Request

|Request endpoint      | Request type | Request parameters |
| -------------------- | ------------ | ------------------ |
| /torrents/{id}/stop  | GET          | `id`: torrent ID   |

##### Response:

Possible `status` values: `success`, `not found`, `not connected`, `not authenticated`

Representation of the torrent with updated fields:

```
{
    'status': 'success',
    'data': {
        'id': 123456,
        'name': 'An.Example.Torrent',
        'status': 0
        'percentDone': 0.42,
        'sizeWhenDone': 1413451432,
        'rateDownload': 3715519,
        'downloadDir': '/opt/transmission-daemon/torrents/download'   
    }
}
```

#### Start torrent

Start specific torrent.

##### Request

|Request endpoint      | Request type | Request parameters |
| -------------------- | ------------ | ------------------ |
| /torrents/{id}/start | GET          | `id`: torrent ID   |

##### Response:

Possible `status` values: `success`, `not found`, `not connected`, `not authenticated`

Representation of the torrent with updated fields:

```
{
    'status': 'success',
    'data': {
        'id': 123456,
        'name': 'An.Example.Torrent',
        'status': 6
        'percentDone': 0.42,
        'sizeWhenDone': 1413451432,
        'rateDownload': 3715519,
        'downloadDir': '/opt/transmission-daemon/torrents/download'   
    }
}
```

#### Delete torrent

Delete specific torrent.

##### Request

|Request endpoint       | Request type | Request parameters |
| --------------------- | ------------ | ------------------ |
| /torrents/{id}/delete | GET          | `id`: torrent ID   |

##### Response:

Possible `status` values: `success`, `not found`, `not connected`, `not authenticated`

Empty response with status string:

```
{
    'status': 'success',
    'data': {}
}
```

#### Add new torrent

Add new torrent.

##### Request

|Request endpoint      | Request type | Request parameters |
| -------------------- | ------------ | ------------------ |
| /torrents/new        | POST         | form data          |

The request should be sent as a form, containing the torrent file and the download location in its data. Only files with the extension of `.torrent` are accepted. The keys for the data are:

- `file` for the torrent file
- `path` for the download location

##### Response:

Possible `status` values: `success`, `no location`, `no file`, `bad file format`, `not connected`, `not authenticated`

Empty response with status string:

```
{
    'status': 'success',
    'data': {}
}
```

### Configuration accessors and modifiers

#### Get/set configuration

The configuration can be described with a JSON object with key-value pairs containing a given setting and its current value. For setting these config values, the client sends a POST request, for getting it sends a GET request. When getting, by default all configuration values will be returned. When setting, only the specified settings will be updated, others will be unchanged. With a first GET request the client knows what settings are available, and can then set them accordingly.

When setting the config, the POST request should contain the new config JSON as its data.

##### Request 

|Request endpoint      | Request type | Request parameters |
| -------------------- | ------------ | ------------------ |
| /config              |  GET         | none               |
| /config              |  POST        | config values      |

The valid configuration values are as the following:

```
{
    "server_address": "192.168.0.2:9091/transmission/rpc",
    "default_download_dir": "/opt/transmission-daemon/torrents/download"
}
```

##### Response

Possible `status` values: `success`, `not connected`, `not authenticated` and `missing key` only for POST request

The response to a GET request will be the config JSON, the response to a POST request will be the usual response JSON, with the data field set to the new config. In case a setting that is not supported by the server was requested, the status field will be set to 'missing key'. Settings that were requested and have valid keys, will be still set.

```
{
    'status': 'success',
    'data':{} 
}
```