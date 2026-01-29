import typer
import pyperclip
import subprocess
import sys
import os
import time
from rich.console import Console
from rich.panel import Panel
from checkpaste.client import CheckpasteClient
from checkpaste.utils import get_local_ip
from checkpaste.config import get_server_info, save_server_info, clear_server_info
from checkpaste.discovery import find_service

console = Console()
cli = typer.Typer()

def get_client(host: str, port: int, password: str = None):
    # If host is default (127.0.0.1) and we have a saved config, use the saved config
    if host == "127.0.0.1" and port == 8000:
        saved = get_server_info()
        if saved:
            return CheckpasteClient(saved["host"], saved["port"], saved.get("password"))
    
    # Otherwise use provided args
    return CheckpasteClient(host, port, password)

@cli.command()
def serve(
    port: int = typer.Option(8000, help="Port to serve on"),
    host: str = typer.Option("0.0.0.0", help="Host interface to bind to"),
    name: str = typer.Option(None, help="Name for auto-discovery (e.g., 'MyPC')"),
    password: str = typer.Option(None, help="Password for authentication"),
    public: bool = typer.Option(False, "--public", help="Expose server to the internet using Ngrok")
):
    """
    Start the checkpaste server.
    """
    local_ip = get_local_ip()
    msg = f"[bold green]checkpaste Server Running[/bold green]\n\nLoopback: http://127.0.0.1:{port}\nNetwork:  http://{local_ip}:{port}"
    
    # Auto-save config for localhost so 'checkpaste sync' works on the host machine too
    save_server_info("127.0.0.1", port, password)
    
    if name:
        msg += f"\nDiscovery: [bold cyan]{name}[/bold cyan]"
    if password:
        msg += f"\nAuth:      [bold red]Enabled[/bold red]"

    if public:
        from pyngrok import ngrok
        public_url = ngrok.connect(port).public_url
        msg += f"\nPublic:   [bold cyan]{public_url}[/bold cyan]  (Global Access)"
    
    msg += "\n\n[yellow]Share this info to connect.[/yellow]"
    console.print(Panel(msg))
    
    # Prepare Environment Variables for the subprocess
    env = os.environ.copy()
    if password:
        env["CHECKPASTE_PASSWORD"] = password
    if name:
        env["CHECKPASTE_NAME"] = name
    if public:
        env["CHECKPASTE_PUBLIC"] = "true"
    env["CHECKPASTE_PORT"] = str(port)

    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "checkpaste.server:app", "--host", host, "--port", str(port)], env=env)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")

@cli.command()
def join(
    name: str = typer.Argument(..., help="Name of the server to join"),
    password: str = typer.Option(None, help="Password if required")
):
    """
    Find and pair with a server on the local network.
    """
    console.print(f"[yellow]Searching for '{name}'...[/yellow]")
    result = find_service(name)
    if result:
        host, port = result
        save_server_info(host, port, password)
        console.print(f"[green]Found and paired with '{name}' at {host}:{port}[/green]")
    else:
        console.print(f"[red]Could not find '{name}' on the network.[/red]")

@cli.command()
def logout():
    """
    Forget the paired server.
    """
    clear_server_info()
    console.print("[green]Disconnected and configuration cleared.[/green]")

@cli.command()
def sync():
    """
    Start Universal Clipboard Sync (Infinite Loop).
    """
    saved = get_server_info()
    if not saved:
        console.print("[red]Not paired with any server. Use 'checkpaste join <NAME>' first.[/red]")
        return
    
    client = CheckpasteClient(saved["host"], saved["port"], saved.get("password"))
    console.print(f"[green]Syncing with server at {saved['host']}:{saved['port']}... (Press Ctrl+C to stop)[/green]")
    
    # Imports for Sync
    from checkpaste.clipboard_utils import get_clipboard_content, set_clipboard_image, set_clipboard_files
    import zipfile
    import io
    import tempfile
    
    last_sync_timestamp = 0.0
    
    # Initialize state
    current_type, current_content = get_clipboard_content()
    # We won't send immediately on startup to avoid loops, just track strict updates.

    try:
        while True:
            try:
                # 1. POLL SERVER
                server_data = client.get_clipboard()
                
                if server_data:
                    server_ts = server_data.get("timestamp", 0.0)
                    server_type = server_data.get("type", "text")
                    
                    # Update Local if Server is newer
                    if server_ts > last_sync_timestamp:
                        console.print(f"[dim]Incoming {server_type}...[/dim]")
                        
                        if server_type == "text":
                            text = server_data.get("text", "")
                            pyperclip.copy(text)
                        
                        elif server_type == "image":
                            filename = server_data.get("filename")
                            img_data = client.get_clipboard_content_file(filename)
                            if img_data:
                                set_clipboard_image(img_data)
                        
                        elif server_type == "files":
                            filename = server_data.get("filename")
                            zip_data = client.get_clipboard_content_file(filename)
                            if zip_data:
                                # Extract to Temp
                                temp_dir = os.path.join(tempfile.gettempdir(), "CheckPaste", str(int(time.time())))
                                os.makedirs(temp_dir, exist_ok=True)
                                
                                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                                    zf.extractall(temp_dir)
                                
                                # Get extracted paths
                                file_paths = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
                                set_clipboard_files(file_paths)
                        
                        last_sync_timestamp = server_ts
                        # Update our local reference to avoid immediate echo-back
                        current_type, current_content = get_clipboard_content()

                # 2. POLL LOCAL
                local_type, local_content = get_clipboard_content()
                
                # Check if changed
                # Equality check for content might be heavy for files/images.
                # Optimized: We assume if type/len changed or text changed.
                # For MVP: Simple comparison.
                
                changed = False
                if local_type != current_type:
                    changed = True
                elif local_type == "text" and local_content != current_content:
                    changed = True
                # For images/files, comparing bytes/lists is okay for now.
                elif local_type == "image" and local_content != current_content:
                     changed = True
                elif local_type == "files" and local_content != current_content:
                     changed = True

                if changed:
                    console.print(f"[dim]Sending {local_type}...[/dim]")
                    
                    success = False
                    if local_type == "text":
                        success = client.send_clipboard_text(local_content)
                    
                    elif local_type == "image":
                        # local_content is PNG bytes
                        success = client.send_clipboard_content("image", local_content, "clipboard_image.png")
                    
                    elif local_type == "files":
                        # local_content is list of paths
                        # Zip them
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            for path in local_content:
                                if os.path.isdir(path):
                                    # Recursive zip for directories
                                    for root, dirs, files in os.walk(path):
                                        for file in files:
                                            abs_path = os.path.join(root, file)
                                            rel_path = os.path.relpath(abs_path, os.path.dirname(path))
                                            zf.write(abs_path, rel_path)
                                else:
                                    zf.write(path, os.path.basename(path))
                        
                        zip_bytes = zip_buffer.getvalue()
                        success = client.send_clipboard_content("files", zip_bytes, "clipboard_files.zip")
                    
                    if success:
                        current_type = local_type
                        current_content = local_content
                        # We expect server ts to update, so we should fetch it or just bump ours?
                        # Ideally server returns new ts. WE should update last_sync_timestamp to match server's
                        # to prevent echo.
                        # client.send methods rely on getting response?
                        # We didn't update client methods to return timestamp. 
                        # That's a tiny flaw. 
                        # Workaround: Sleep briefly so next poll gets own message (and ignored if content matches? No logic relies on TS).
                        # Actually logic relies on TS.
                        # If I send, Server TS updates. 
                        # Next poll: Server TS > Last Sync TS.
                        # I receive my own message.
                        # I overwrite local clipboard. 
                        # If content is same, usually benign (flicker).
                        # Best fix: Update last_sync_timestamp to now() locally?
                        last_sync_timestamp = time.time() 

            except Exception as e:
                # console.print(f"[red]Sync error: {e}[/red]")
                pass
            
            time.sleep(1) 
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Sync stopped.[/yellow]")

@cli.command()
def copy(
    text: str = typer.Argument(None, help="Text to send. If not provided, reads from local clipboard."),
    host: str = typer.Option("127.0.0.1", help="Host IP"),
    port: int = typer.Option(8000, help="Port"),
    password: str = typer.Option(None, help="Password")
):
    """
    Send text to the checkpaste server.
    """
    client = get_client(host, port, password)
    
    if text is None:
        text = pyperclip.paste()
        if not text:
            console.print("[red]Clipboard is empty and no text provided.[/red]")
            return

    if client.send_clipboard(text):
        console.print(f"[green]Successfully sent text![/green]")
    else:
        console.print("[red]Failed to send text.[/red]")

@cli.command()
def paste(
    host: str = typer.Option("127.0.0.1", help="Host IP"),
    port: int = typer.Option(8000, help="Port"),
    password: str = typer.Option(None, help="Password")
):
    """
    Retrieve text from the checkpaste server.
    """
    client = get_client(host, port, password)
    text = client.get_clipboard()
    if text:
        pyperclip.copy(text)
        console.print(f"[green]Fetched text and copied to clipboard![/green]")
        console.print(f"[dim]Content: {text}[/dim]")
    else:
        console.print("[red]Failed to fetch or clipboard empty.[/red]")

@cli.command()
def send_file(
    file_path: str = typer.Argument(..., help="Path to the file to send"),
    host: str = typer.Option("127.0.0.1", help="Host IP"),
    port: int = typer.Option(8000, help="Port"),
    password: str = typer.Option(None, help="Password")
):
    """
    Send a file to the checkpaste server.
    """
    import os
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn

    file_size = os.path.getsize(file_path)
    client = get_client(host, port, password)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Sending {os.path.basename(file_path)}...", total=file_size)
        
        def update_progress(bytes_sent):
            progress.update(task, advance=bytes_sent)

        if client.send_file(file_path, progress_callback=update_progress):
             console.print(f"[green]Successfully sent file '{file_path}'![/green]")
        else:
             console.print("[red]Failed to send file.[/red]")

@cli.command()
def get_file(
    filename: str = typer.Argument(..., help="Name of the file to download"),
    host: str = typer.Option("127.0.0.1", help="Host IP"),
    port: int = typer.Option(8000, help="Port"),
    password: str = typer.Option(None, help="Password")
):
    """
    Download a file from the checkpaste server.
    """
    client = get_client(host, port, password)
    downloaded = client.download_file(filename)
    if downloaded:
        console.print(f"[green]Successfully downloaded '{downloaded}'![/green]")
    else:
        console.print("[red]Failed to download file.[/red]")

@cli.command()
def list_files(
    host: str = typer.Option("127.0.0.1", help="Host IP"),
    port: int = typer.Option(8000, help="Port"),
    password: str = typer.Option(None, help="Password")
):
    """
    List available files on the checkpaste server.
    """
    client = get_client(host, port, password)
    files = client.list_files()
    if files:
        console.print(Panel("\n".join(files), title="Available Files"))
    else:
        console.print("[yellow]No files found on server.[/yellow]")

def app():
    cli()
    
if __name__ == "__main__":
    app()
