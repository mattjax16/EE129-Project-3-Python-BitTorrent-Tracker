from flask import Flask, request, jsonify
import time
import signal
import sys
from dataclasses import dataclass
from typing import Dict, Set, Optional
import urllib.parse
import threading
import bencodepy
import codecs




@dataclass(eq=True, frozen=True)
class Peer:
    peer_id: str
    ip: str
    port: int
    last_seen: float
    uploaded: int = 0
    downloaded: int = 0
    left: int = 0
    is_seeder: bool = False


@dataclass
class TorrentInfo:
    info_hash: str
    name: str = ""
    size: int = 0
    piece_length: int = 0
    creation_date: float = 0.0
    comment: str = ""
    created_by: str = ""


class Tracker:
    def __init__(self):
        self.torrents: Dict[str, Set[Peer]] = {}
        self.torrent_info: Dict[str, TorrentInfo] = {}

    def add_torrent(self, info_hash: str, name: str = "", size: int = 0,
                    piece_length: int = 0, comment: str = "", created_by: str = ""):
        """Add or update torrent information."""
        if info_hash not in self.torrent_info:
            self.torrent_info[info_hash] = TorrentInfo(
                info_hash=info_hash,
                name=name,
                size=size,
                piece_length=piece_length,
                creation_date=time.time(),
                comment=comment,
                created_by=created_by
            )
        if info_hash not in self.torrents:
            self.torrents[info_hash] = set()

    def add_peer(self, info_hash: str, peer_id: str, ip: str, port: int,
                 uploaded: int = 0, downloaded: int = 0, left: int = 0):

        """Add or update a peer for a specific torrent."""
        if info_hash not in self.torrents:
            self.add_torrent(info_hash)

        # Remove old peer entry if it exists
        self.torrents[info_hash] = {
            p for p in self.torrents[info_hash]
            if p.peer_id != peer_id
        }

        # Add new peer entry
        new_peer = Peer(
            peer_id=peer_id,
            ip=ip,
            port=port,
            last_seen=time.time(),
            uploaded=uploaded,
            downloaded=downloaded,
            left=left,
            is_seeder=left == 0
        )
        self.torrents[info_hash].add(new_peer)

    def get_peers(self, info_hash: str, requesting_peer_id: Optional[str] = None) -> Set[Peer]:
        """Get all peers for a torrent except the requesting peer."""
        if info_hash not in self.torrents:
            return set()

        peers = self.torrents[info_hash]

        # Remove peers that haven't been seen in 30 minutes
        current_time = time.time()
        active_peers = {
            peer for peer in peers
            if current_time - peer.last_seen < 1800
        }
        self.torrents[info_hash] = active_peers

        # Don't return the requesting peer in the peer list
        if requesting_peer_id:
            return {
                peer for peer in active_peers
                if peer.peer_id != requesting_peer_id
            }
        return active_peers

    def get_stats(self, info_hash: str) -> dict:
        """Get detailed statistics for a torrent."""
        if info_hash not in self.torrents:
            return {}

        peers = self.get_peers(info_hash)
        seeders = sum(1 for p in peers if p.is_seeder)
        leechers = len(peers) - seeders

        total_uploaded = sum(p.uploaded for p in peers)
        total_downloaded = sum(p.downloaded for p in peers)

        return {
            'complete': seeders,
            'incomplete': leechers,
            'downloaded': total_downloaded,
            'uploaded': total_uploaded,
            'peers': len(peers)
        }

    def save_state(self):
        """Save tracker state before shutdown."""
        print("\nSaving tracker state...")
        print(f"Active torrents: {len(self.torrents)}")
        for info_hash, peers in self.torrents.items():
            stats = self.get_stats(info_hash)
            torrent_info = self.torrent_info.get(info_hash, TorrentInfo(info_hash))
            print(f"Torrent {torrent_info.name or info_hash}:")
            print(f"  Peers: {stats['peers']}")
            print(f"  Seeders: {stats['complete']}")
            print(f"  Leechers: {stats['incomplete']}")
            print(f"  Total uploaded: {stats['uploaded']}")
            print(f"  Total downloaded: {stats['downloaded']}")


app = Flask(__name__)
tracker = Tracker()
shutdown_event = threading.Event()


# Default root (sends to announce)
@app.route('/', methods=['GET'])
def root_announce():
    return announce()  # Reuse the existing announce function

@app.route('/announce', methods=['GET'])
def announce():
    try:
        # Parse required parameters
        info_hash = request.args.get('info_hash')







        peer_id = request.args.get('peer_id')
        port = int(request.args.get('port'))
        uploaded = int(request.args.get('uploaded', 0))
        downloaded = int(request.args.get('downloaded', 0))
        left = int(request.args.get('left', 0))
        event = request.args.get('event')

        if not all([info_hash, peer_id, port]):
            return jsonify({'error': 'Missing required parameters'}), 400

        # Get peer IP from request
        ip = request.remote_addr

        # Update peer in tracker
        tracker.add_peer(info_hash, peer_id, ip, port, uploaded, downloaded, left)

        # Get peer list
        peers = tracker.get_peers(info_hash, peer_id)
        stats = tracker.get_stats(info_hash)

        # Format response
        peer_list = [{
            'peer_id': p.peer_id,
            'ip': p.ip,
            'port': p.port
        } for p in peers]

        return_vals = {
            'interval': 1800,
            'complete': stats['complete'],
            'incomplete': stats['incomplete'],
            'peers': peer_list
        }

        return bencodepy.encode(return_vals)


    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/scrape', methods=['GET'])
def scrape():
    try:
        info_hash = request.args.get('info_hash')
        if not info_hash:
            return jsonify({'error': 'Missing info_hash parameter'}), 400

        stats = tracker.get_stats(info_hash)
        torrent_info = tracker.torrent_info.get(info_hash)

        response = {
            'files': {
                info_hash: {
                    'complete': stats['complete'],
                    'downloaded': stats['downloaded'],
                    'incomplete': stats['incomplete'],
                    'name': torrent_info.name if torrent_info else "",
                }
            }
        }


        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/add_torrent', methods=['POST'])
def add_torrent():
    """Add a new torrent to the tracker."""
    try:
        data = request.get_json()
        if not data or 'info_hash' not in data:
            return jsonify({'error': 'Missing info_hash'}), 400

        tracker.add_torrent(
            info_hash=data['info_hash'],
            name=data.get('name', ''),
            size=data.get('size', 0),
            piece_length=data.get('piece_length', 0),
            comment=data.get('comment', ''),
            created_by=data.get('created_by', '')
        )

        return jsonify({'message': 'Torrent added successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get detailed statistics for all torrents."""
    try:
        stats = {}
        for info_hash in tracker.torrents:
            torrent_info = tracker.torrent_info.get(info_hash)
            torrent_stats = tracker.get_stats(info_hash)
            stats[info_hash] = {
                'name': torrent_info.name if torrent_info else "",
                'size': torrent_info.size if torrent_info else 0,
                'creation_date': torrent_info.creation_date if torrent_info else 0,
                'stats': torrent_stats
            }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Endpoint to trigger graceful shutdown."""
    shutdown_event.set()
    return jsonify({'message': 'Server shutting down...'})


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}")
    tracker.save_state()
    shutdown_event.set()


def run_server(host='0.0.0.0', port=6969):
    """Run the server in a separate thread so we can monitor the shutdown event."""
    from werkzeug.serving import run_simple
    run_simple(host, port, app, threaded=True)


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        print("Starting BitTorrent tracker on port 6969...")
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        # Wait for shutdown signal
        while not shutdown_event.is_set():
            time.sleep(1)

        print("Shutting down server...")
        tracker.save_state()
        sys.exit(0)

    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)