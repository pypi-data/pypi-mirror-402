# SnapFS Scanner Agent

The **SnapFS Scanner Agent** runs file system scans on machines that have
direct access to storage (local disks, network mounts, etc.).

## What it does

- Runs `snapfs scan` locally on demand
- Works with local filesystems and mounted storage
- Runs continuously in the background
- Designed for servers, NAS hosts, and storage-adjacent machines

The agent does **not**:
- schedule scans itself
- publish scan results directly
- require special filesystem access beyond what `snapfs` needs

---

## Requirements

- Python 3.8+
- The `snapfs` CLI installed and available on `PATH`
- Network access

## Installation

### Using pip

```
pip install snapfs-agent-scanner snapfs
```

Run the agent:

```
snapfs-agent-scanner
```

With explicit configuration:

```
snapfs-agent-scanner \
  --gateway https://localhost:8000 \
  --agent-id scanner-01 \
  --scan-root /mnt/data
```

## Docker

```
docker run --rm \
  -e SNAPFS_AGENT_ID=scanner-01 \
  -e SNAPFS_SCAN_ROOT=/mnt/data \
  -e GATEWAY_WS=ws://gateway:8000 \
  -v /mnt/data:/mnt/data \
  ghcr.io/snapfsio/snapfs-agent-scanner:latest
```

The container runs the scanner agent continuously and executes scans when requested.

## Running as a Systemd Service (Linux)

The agent includes a simple systemd service for Linux hosts.

Install and enable it:

```
sudo ./systemd/install.sh
```

To uninstall:

```
sudo ./systemd/uninstall.sh
```

## Configuration

The agent can be configured using **CLI flags** or **environment variables**.

### CLI Options

```
snapfs-agent-scanner [options]

--gateway <url>        Gateway URL (http/https/ws/wss)
--gateway-ws <url>     Explicit WebSocket URL
--ws-path <path>       Gateway path (default: /agents)
--agent-id <id>        Stable identifier for this agent
--scan-root <path>     Filesystem root to scan
--version              Print version and exit
```

### Environment Variables

```
GATEWAY_WS          Gateway WebSocket URL
GATEWAY_HTTP        Reserved for future use
SNAPFS_AGENT_ID     Agent identifier
SNAPFS_SCAN_ROOT    Filesystem root for scans
```
