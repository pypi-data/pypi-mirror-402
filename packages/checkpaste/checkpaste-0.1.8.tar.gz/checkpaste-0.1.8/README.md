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

### 1. Start Server (Host)
On your main computer:
```bash
checkpaste serve --name "MyPC" --password "secret123"
```

### 2. Connect (Client)
On your other devices (Phone, Laptop, Raspberry Pi):
```bash
checkpaste join "MyPC" --password "secret123"
```
*(This finds the server automatically and saves the connection)*

### 3. Universal Clipboard (Sync)
To sync clipboards in real-time (copy here -> paste there):
```bash
checkpaste sync
```
*(Keep this running in the background)*

### 4. Manual Transfer
Once joined, you can also send/get files manually without typing IPs:
```bash
checkpaste copy "Hello World"
checkpaste paste
checkpaste send-file photo.jpg
checkpaste get-file photo.jpg
checkpaste list-files
```

### 5. Disconnect
```bash
checkpaste logout
```
