# checkpaste

**checkpaste** is a lightweight, cross-platform Python CLI tool that allows you to copy text or files on one device and paste/download them on another device within the same local network.

## Features
- **Sync Clipboard**: Copy text on one machine, paste on another.
- **Send Files**: Easily transfer files between devices.
- **Cross-Platform**: Works on Windows, macOS, Linux, and Raspberry Pi.
- **Local Network**: Fast and secure transfer over LAN.

## Installation

```bash
pip install checkpaste
```

## Usage

### Host (Server)
Start the checkpaste server on one device:
```bash
checkpaste serve
```

### Client
Copy text to the server:
```bash
checkpaste copy "Hello from Windows"
```

Get text from the server:
```bash
checkpaste paste
```

Send a file:
```bash
checkpaste send-file path/to/file.txt
```
