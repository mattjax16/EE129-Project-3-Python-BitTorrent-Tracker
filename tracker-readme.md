# Simple BitTorrent Tracker

A lightweight, Flask-based BitTorrent tracker implementation with persistent state storage.

## Features

- Fully compliant with BitTorrent protocol specification
- Support for announce and scrape requests
- Persistent state storage using JSON
- Real-time peer tracking and management
- Hash similarity matching for improved torrent identification
- Built-in support for statistics and monitoring
- Graceful shutdown handling
- Thread-safe operations

## Requirements

```
flask
bencodepy
```

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install flask bencodepy
```

## Configuration

### 1. Tracker (tracker.py)

The main tracker file contains several important configuration variables that control its behavior:

```python
# Network Configuration
IP = '0.0.0.0'  # Interface to bind to
PORT = 6969     # Port number for the tracker

# Timeout Settings
PEER_TIMEOUT = 1800  # 30 minutes in seconds

# Hash Matching Configuration
HASH_SIMILARITY_THRESHOLD = 0.95  # 95% similarity threshold

# State Management
DATA_FILE = "tracker_state.json"  # State file location
```

#### Variable Descriptions

1. **Network Configuration**
   - `IP`: 
     - Default: '0.0.0.0'
     - Purpose: Determines which network interface the tracker binds to
     - Options:
       - '0.0.0.0': Listen on all interfaces
       - '127.0.0.1': Listen only on localhost
       - Specific IP: Listen on a specific interface

   - `PORT`:
     - Default: 6969
     - Purpose: The port number the tracker service listens on
     - Note: Should be open in firewall if using remote connections

2. **Timeout Settings**
   - `PEER_TIMEOUT`:
     - Default: 1800 seconds (30 minutes)
     - Purpose: Time after which inactive peers are removed
     - Impact: Affects peer list cleanup and resource usage
     - Considerations:
       - Lower values: More aggressive cleanup, less memory usage
       - Higher values: Better peer persistence, more memory usage

3. **Hash Matching Configuration**
   - `HASH_SIMILARITY_THRESHOLD`:
     - Default: 0.95 (95% similarity)
     - Purpose: Controls how strictly torrent hashes are matched
     - Impact: Affects torrent deduplication and identification
     - Settings:
       - Higher values (0.99): Stricter matching, fewer false positives
       - Lower values (0.90): More lenient matching, possible false positives

4. **State Management**
   - `DATA_FILE`:
     - Default: "tracker_state.json"
     - Purpose: Where tracker state is saved and loaded from
     - Format: JSON file containing all tracker state
     - Considerations:
       - Use absolute paths in production
       - Ensure write permissions
       - Consider backup location

#### Server Configuration Method

```python
def run_server(host='0.0.0.0', port=6969):
    """
    Main server configuration method
    
    Args:
        host (str): Interface to bind to
        port (int): Port to listen on
    """
    app.run(
        host=host,
        port=port,
        threaded=True,  # Enable multi-threading
        use_reloader=False  # Disable auto-reloader
    )
```

### 2. Torrent Info Script (add_torrent_info.py)

The script for adding torrents to the tracker has several configuration variables:

```python
# Tracker Configuration
TRACKER_DEFAULT_URL = 'http://localhost:6969'
TRACKER_ENDPOINT = '/add_torrent_info'

# Encoding Settings
ENCODING = 'utf-8'
DEFAULT_CREATED_BY = 'Torrent Tracker Script'

# Error Handling Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# File Processing Configuration
CHUNK_SIZE = 8192  # bytes for reading large files
SUPPORTED_EXTENSIONS = ['.torrent']

# HTTP Request Configuration
REQUEST_TIMEOUT = 30  # seconds
HTTP_HEADERS = {
    'User-Agent': 'Torrent-Tracker-Client/1.0',
    'Content-Type': 'application/json'
}
```

#### Variable Descriptions

1. **Tracker Configuration**
   - `TRACKER_DEFAULT_URL`:
     - Default: 'http://localhost:6969'
     - Purpose: Base URL for the tracker
     - Can be overridden via command line argument
   
   - `TRACKER_ENDPOINT`:
     - Default: '/add_torrent_info'
     - Purpose: API endpoint for adding torrent information
     - Used in conjunction with TRACKER_DEFAULT_URL

2. **Encoding Settings**
   - `ENCODING`:
     - Default: 'utf-8'
     - Purpose: Character encoding for torrent metadata
     - Used when decoding torrent file strings
   
   - `DEFAULT_CREATED_BY`:
     - Default: 'Torrent Tracker Script'
     - Purpose: Default value for created_by field
     - Used when torrent file lacks this information

3. **Error Handling Configuration**
   - `MAX_RETRIES`:
     - Default: 3
     - Purpose: Number of attempts to add a torrent
     - Impact: Affects reliability vs speed tradeoff
   
   - `RETRY_DELAY`:
     - Default: 2 seconds
     - Purpose: Wait time between retry attempts
     - Helps prevent overwhelming the tracker

4. **File Processing Configuration**
   - `CHUNK_SIZE`:
     - Default: 8192 bytes
     - Purpose: Buffer size for reading large files
     - Impact: Memory usage vs read performance
   
   - `SUPPORTED_EXTENSIONS`:
     - Default: ['.torrent']
     - Purpose: List of valid file extensions
     - Used for initial file validation

5. **HTTP Request Configuration**
   - `REQUEST_TIMEOUT`:
     - Default: 30 seconds
     - Purpose: Maximum time to wait for tracker response
     - Prevents indefinite hanging on slow connections
   
   - `HTTP_HEADERS`:
     - Default: User-Agent and Content-Type headers
     - Purpose: HTTP request metadata
     - Identifies client and specifies JSON content

### 3. State Management

The tracker uses a JSON-based state management system with the following characteristics:

1. **Automatic State Saving**
   - Saves on clean shutdown
   - Saves on receiving SIGINT/SIGTERM
   - Periodic automatic saves (configurable)

2. **State File Format**
   ```json
   {
     "torrents": {
       "info_hash": {
         "info": {
           "name": "torrent_name",
           "size": 1234567,
           "piece_length": 262144
         },
         "peers_info": [...],
         "stats": {...}
       }
     }
   }
   ```

3. **Recovery Behavior**
   - Loads last known state on startup
   - Cleans up stale peers during load
   - Creates new state file if none exists

### Server Configuration

#### Network Settings
```python
def run_server(host='0.0.0.0', port=6969):
    """
    host: Interface to bind to (0.0.0.0 for all interfaces)
    port: Port number for the tracker
    """
    app.run(
        host=host,
        port=port,
        threaded=True,  # Enable multi-threading
        use_reloader=False  # Disable auto-reloader
    )
```

### State Management

The tracker manages state in several ways:

1. **Persistence Configuration**
   - State file location: Configured via `DATA_FILE` variable
   - Default path: `tracker_state.json` in working directory
   - Custom path example: `DATA_FILE = "/var/lib/tracker/state.json"`

2. **Peer Management**
   - Peer timeout: `PEER_TIMEOUT = 1800` (30 minutes)
   - Peers inactive longer than this are automatically removed
   - Adjust this value based on your network conditions

3. **Hash Matching**
   - Similarity threshold: `HASH_SIMILARITY_THRESHOLD = 0.95`
   - Affects torrent identification and deduplication
   - Lower values are more lenient, higher values more strict

### Environment Variables

You can override default settings using environment variables:

```bash
# Example environment variable configuration
export TRACKER_IP="127.0.0.1"
export TRACKER_PORT="6969"
export TRACKER_DATA_FILE="/path/to/state.json"
export TRACKER_PEER_TIMEOUT="3600"
```

### Production Configuration

For production deployments, recommended settings:

1. **Security**
   ```python
   IP = '127.0.0.1'  # Only accept local connections if behind reverse proxy
   DATA_FILE = '/var/lib/tracker/state.json'  # Use proper system path
   ```

2. **Performance**
   ```python
   PEER_TIMEOUT = 3600  # Increase timeout for better persistence
   HASH_SIMILARITY_THRESHOLD = 0.98  # Stricter matching for production
   ```

3. **Logging**
   - Configure Flask logging level
   - Set up system logging
   - Enable request logging

### Development Configuration

For development and testing:

```python
IP = '0.0.0.0'  # Accept connections from anywhere
PORT = 6969     # Standard development port
DATA_FILE = 'dev_tracker_state.json'  # Separate development state file
PEER_TIMEOUT = 300  # 5 minutes for faster testing
```

## Usage

### Starting the Tracker

Run the tracker using:

```bash
python tracker.py
```

The tracker will start on port 6969 by default.

### API Endpoints

#### 1. Announce (`/announce` or `/`)
- Method: GET
- Required Parameters:
  - info_hash: Torrent info hash
  - peer_id: Unique peer identifier
  - port: Peer's listening port
- Optional Parameters:
  - uploaded: Amount uploaded
  - downloaded: Amount downloaded
  - left: Amount left to download
  - event: Event type

#### 2. Scrape (`/scrape`)
- Method: GET
- Required Parameters:
  - info_hash: Torrent info hash
- Returns torrent statistics including number of seeders and leechers

#### 3. Add Torrent Info (`/add_torrent_info`)
- Method: POST
- Required JSON Body:
  - info_hash: Torrent info hash
- Optional JSON Fields:
  - name: Torrent name
  - size: Total size
  - piece_length: Size of each piece
  - comment: Torrent comment
  - created_by: Creator information

#### 4. Statistics (`/stats`)
- Method: GET
- Returns detailed statistics for all tracked torrents

#### 5. Save State (`/save_state`)
- Method: GET
- Manually triggers state save to disk

#### 6. Shutdown (`/shutdown`)
- Method: POST
- Triggers graceful server shutdown

## Features in Detail

### Persistent State Storage
The tracker maintains state between restarts by saving all torrent and peer information to a JSON file. This includes:
- Active torrents
- Peer information
- Upload/download statistics
- Torrent metadata

### Hash Similarity Matching
The tracker implements a hash similarity feature that helps identify identical torrents with slightly different info hashes. This is done by:
- Comparing first 10 and last 5 characters of info hashes
- Using a configurable similarity threshold
- Automatically merging similar torrent entries

### Peer Management
- Automatic cleanup of inactive peers
- Tracking of seeder/leecher status
- Real-time peer statistics
- Support for peer ID rotation

## Error Handling

The tracker implements comprehensive error handling:
- Input validation for all endpoints
- Exception handling for network operations
- Graceful degradation on state file corruption
- Automatic recovery mechanisms

## Security Considerations

- The tracker runs on all interfaces by default (0.0.0.0)
- No authentication is implemented
- Consider running behind a reverse proxy for production use
- Implement appropriate firewall rules

## Monitoring

The tracker provides real-time statistics through the `/stats` endpoint, including:
- Number of active torrents
- Peer counts
- Upload/download statistics
- Seeder/leecher ratios

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues and feature requests, please create an issue in the repository.