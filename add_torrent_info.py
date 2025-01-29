import bencodepy  # pip install bencodepy
import hashlib
import os
import requests
import argparse
from typing import Dict, Any
import time

# Global Configuration
TRACKER_DEFAULT_URL = 'http://localhost:6969'
TRACKER_ENDPOINT = '/add_torrent_info'
ENCODING = 'utf-8'
DEFAULT_CREATED_BY = 'Torrent Tracker Script'

# Error handling configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# File processing configuration
CHUNK_SIZE = 8192  # bytes for reading large files
SUPPORTED_EXTENSIONS = ['.torrent']

# HTTP request configuration
REQUEST_TIMEOUT = 30  # seconds
HTTP_HEADERS = {
    'User-Agent': 'Torrent-Tracker-Client/1.0',
    'Content-Type': 'application/json'
}


def read_torrent_file(torrent_path: str) -> Dict[str, Any]:
    """Read and parse a .torrent file."""
    try:
        with open(torrent_path, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
        return torrent_data
    except IOError as e:
        raise IOError(f"Failed to read torrent file: {e}")
    except bencodepy.DecodingError as e:
        raise ValueError(f"Invalid torrent file format: {e}")


def custom_urlencode(data):
    """URL encode binary data with custom formatting."""
    result = []
    for byte in data:
        # Check if the byte is a printable ASCII character (0x20 to 0x7E)
        if 0x20 <= byte <= 0x7e:
            result.append(chr(byte))
        else:
            # Percent-encode with uppercase hex digits
            result.append(f'%{byte:02X}')
    return ''.join(result)


def calculate_info_hash(torrent_data: Dict[str, Any]) -> str:
    """Calculate the info hash of a torrent."""
    info_dict = torrent_data.get(b'info', {})
    bencode_encoded_info = bencodepy.encode(info_dict)
    sha1_encoded_info_bin = hashlib.sha1(bencode_encoded_info).digest()
    return custom_urlencode(sha1_encoded_info_bin)


def get_torrent_name(torrent_data: Dict[str, Any]) -> str:
    """Get the name of the torrent."""
    info_dict = torrent_data.get(b'info', {})
    name = info_dict.get(b'name', b'').decode(ENCODING, errors='replace')
    return name


def get_torrent_size(torrent_data: Dict[str, Any]) -> int:
    """Calculate total size of the torrent."""
    info_dict = torrent_data.get(b'info', {})

    # Single file mode
    if b'length' in info_dict:
        return info_dict[b'length']

    # Multi file mode
    elif b'files' in info_dict:
        return sum(file[b'length'] for file in info_dict[b'files'])

    return 0


def add_torrent_to_tracker(tracker_url: str, torrent_path: str) -> None:
    """Add a torrent to the tracker with retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            # Read and parse the torrent file
            torrent_data = read_torrent_file(torrent_path)

            # Extract metadata
            info_hash = calculate_info_hash(torrent_data)
            name = get_torrent_name(torrent_data)
            size = get_torrent_size(torrent_data)
            piece_length = torrent_data.get(b'info', {}).get(b'piece length', 0)
            comment = torrent_data.get(b'comment', b'').decode(ENCODING, errors='replace')
            created_by = torrent_data.get(b'created by', DEFAULT_CREATED_BY.encode()).decode(ENCODING, errors='replace')
            creation_date = torrent_data.get(b'creation date', int(time.time()))

            # Prepare the payload
            payload = {
                'info_hash': info_hash,
                'name': name,
                'size': size,
                'piece_length': piece_length,
                'comment': comment,
                'created_by': created_by,
                'creation_date': creation_date
            }

            # Send to tracker
            response = requests.post(
                f"{tracker_url}{TRACKER_ENDPOINT}",
                json=payload,
                headers=HTTP_HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()
            print(f"Successfully added torrent info for {name}")
            return

        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Attempt {attempt + 1} failed. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Failed to add torrent after {MAX_RETRIES} attempts: {e}")
        except Exception as e:
            print(f"Error adding torrent: {e}")
            break


def validate_torrent_file(torrent_path: str) -> bool:
    """Validate torrent file path and extension."""
    if not os.path.exists(torrent_path):
        print(f"Error: File not found: {torrent_path}")
        return False

    _, ext = os.path.splitext(torrent_path)
    if ext.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file extension: {ext}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description='Add torrents to the tracker')
    parser.add_argument('torrent_files', nargs='+', help='Path to .torrent file(s)')
    parser.add_argument('--tracker', default=TRACKER_DEFAULT_URL,
                        help=f'Tracker URL (default: {TRACKER_DEFAULT_URL})')

    args = parser.parse_args()

    for torrent_file in args.torrent_files:
        if validate_torrent_file(torrent_file):
            print(f"\nProcessing: {torrent_file}")
            add_torrent_to_tracker(args.tracker, torrent_file)


if __name__ == '__main__':
    main()