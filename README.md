# Python-BitTorrent-Tracker

A lightweight BitTorrent tracker implementation with persistent state management.

### Why This Tracker?

This project was created as an easy way to set up a private BitTorrent tracker for distributing torrents while maintaining
an extra layer of privacy. While no one should be able to access a torrent without its corresponding `.torrent` file,
using a private tracker ensures that peers only communicate through a controlled environment, without relying
on the Distributed Hash Table (DHT) or public trackers. This makes it useful for cases where you want to share
torrents securely while avoiding unnecessary exposure to public networks.

### What I Learned

While building this tracker, I gained a deeper understanding of networking concepts, particularly in
implementing application-layer protocols. The BitTorrent protocol itself requires handling structured
peer communication through HTTP-based announce requests and responses. Additionally, I had to implement
techniques like:

- **_Bencoding:_** A unique encoding format used by BitTorrent for serializing data efficiently.
- **_SHA-1 Hashing:_** Used to generate and verify torrent info hashes, ensuring data integrity.
- **_State Management & Persistence:_** Keeping track of peers, torrents, and session data while ensuring that state is preserved across restarts.

## Features

### Tracker Server

- ✅ Peer announcements (`/announce`)
- 📊 Torrent statistics scraping (`/scrape`)
- ➕ Torrent metadata registration (`/add_torrent_info`)
- 💾 State persistence to disk (JSON format `tracker_state.json` by default)
- 🔍 Similar hash detection (first 10 and last 5 characters by default with ability to adjust tolerances)
- 🧹 Automatic peer cleanup (30-minute inactivity window by default)

### Client Script

- 📁 Torrent file parsing (.torrent)
- 🔗 Info hash calculation with custom URL encoding
- 📋 Metadata extraction (name, size, creation date, etc.)
- 🔄 Retry mechanism for failed requests (3 attempts)
- 📦 Batch processing of multiple torrent files

## Requirements

```
flask
bencodepy
requests
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mattjax16/Python-BitTorrent-Tracker.git
   cd Python-BitTorrent-Tracker
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Tracker Usage

### Starting the Tracker

```bash
python tracker.py
```

Server runs on http://localhost:6969 by default

Tp shut down the server, use `Ctrl+C` and it will save the state (what torrents its tracking and their peer lists) automatically to `tracker_state.json`.

## API Endpoints

| Endpoint          | Method | Description                     |
| ----------------- | ------ | ------------------------------- |
| /add_torrent_info | POST   | Register torrent metadata       |
| /announce         | GET    | Peer announcement endpoint      |
| /scrape           | GET    | Get torrent statistics          |
| /stats            | GET    | Get detailed tracker statistics |
| /save_state       | GET    | Manually trigger state save     |
| /shutdown         | POST   | Graceful server shutdown        |

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
     - _This is the standard port for bittorrent trackers_

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

## Client Script Usage (add_torrent_info.py)

The client script is used to add torrent metadata to the tracker. It supports batch processing of multiple torrent files.

### Basic Usage

```bash
python add_torrent_info.py <torrent_file>
```

### Batch Processing

```bash
python add_torrent_info.py <directory>
```

### Command Line Arguments

- `<torrent_file(s)>`: Path to a single torrent file (or multiple files)
- `-t`, `--tracker`: Tracker URL (default: http://localhost:6969)

---

# Complete Example Usage

This guide provides clear step-by-step guidance for setting up the tracker, creating torrents, adding torrent info,
and checking tracker statistics.

> **Note**: Throughout this guide, `<tracker-ip>` is a placeholder. Replace it with the actual IP address shown in your console when starting the tracker server.

### Installation

1. **Clone the Repository**

```bash
git clone https://github.com/mattjax16/Python-BitTorrent-Tracker.git
cd Python-BitTorrent-Tracker
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### Setting Up the Tracker

1. **Start the tracker server** (default port: `6969`)

```bash
python tracker.py
```

The tracker will now listen for peer announcements and manage torrents. The console will display the tracker's IP
address - note this down as you'll need it for all following steps.

2. **Verify the tracker is running** by checking its status:

```bash
curl http://<tracker-ip>:6969/stats
```

If everything is set up correctly, this should return an empty tracker state at first.

### Creating a Torrent & Announcing to the Tracker

1. **Create a `.torrent` file**
   You can use any BitTorrent client to create a torrent file, though [qBittorrent](https://www.qbittorrent.org/) is recommended as it's free, open-source, and user-friendly. When creating the torrent:

- In the tracker address field, make sure to specify your tracker's IP and port with the full URL format: `http://<tracker-ip>:6969/announce`
  - The `http://` prefix is essential - don't forget it!
  - Replace `<tracker-ip>` with the IP address that was shown when you started the tracker server

For enhanced privacy, you can disable DHT (Distributed Hash Table) network distribution. The DHT network is a decentralized
way for peers to find each other without a tracker, but disabling it ensures that only peers connected to your private
tracker can participate in sharing.

2. **Announce to the tracker** (from a BitTorrent client)
   - Load `example.torrent` into a torrent client (e.g., [qBittorrent](https://www.qbittorrent.org/), [Transmission](https://transmissionbt.com/))
   - The client will send an **announce** request to `http://<tracker-ip>:6969/announce`
   - The tracker will now list this torrent along with the connected peers

### Checking Tracker Statistics

1. **Retrieve torrent statistics** using the scrape API:

```bash
curl "http://<tracker-ip>:6969/scrape?info_hash=<info_hash>"
```

This returns seeders, leechers, and completed downloads for the given torrent. `<info_hash>` is the SHA-1 hash of the torrent's info dictionary.

2. **Get a full tracker overview**:

```bash
curl "http://<tracker-ip>:6969/stats"
```

This displays all active torrents and their peer lists.

### Adding Torrent Info Manually

1. **Manually register a torrent's metadata**:

```bash
python add_torrent_info.py example.torrent
```

This extracts torrent details and sends them to the tracker's `/add_torrent_info` endpoint.


### Announcing Another Peer (From a Different Computer)

When another user wants to download the torrent:

1. **Load the torrent file on the second computer**

   - Copy the `.torrent` file to the second computer
   - Open it with a BitTorrent client (like qBittorrent)
   - The client will automatically send an announce request to the tracker URL specified in the torrent file
   - Note: The torrent file already contains the correct tracker IP address you specified when creating it

2. **Verify both peers are connected**:

```bash
curl "http://<tracker-ip>:6969/stats"
```

You'll see two peers listed for the torrent:

- The original peer (showing as a "seeder") who has the complete file and is uploading
- The new peer (showing as a "leecher") who is currently downloading

The tracker facilitates this connection, allowing the seeder to share the files with the leecher. As the download
progresses, you'll see the leecher's "downloaded" and "left" values change in the stats. Once the download completes,
the leecher will automatically become another seeder in the swarm.
