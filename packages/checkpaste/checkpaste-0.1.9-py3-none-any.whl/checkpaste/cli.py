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
    
    last_sync_content = pyperclip.paste() # Initialize with current clipboard
    
    # We need to be careful not to send what we just received.
    # We will use a simple state tracking.
    
    try:
        while True:
            try:
                # 1. POLL SERVER
                # We fetch from server.
                server_content = client.get_clipboard()
                
                # 2. READ LOCAL
                local_content = pyperclip.paste()
                
                # Case A: Server has new content (different from what we last knew)
                # AND it is different from our local content (meaning we didn't just copy it)
                # Wait, if Server changed, we WANT to overwrite local.
                # But what if we just copied something locally 0.1s ago?
                # Conflict resolution: Last Write Wins.
                # Since we don't have perfect timestamps from os, we prioritize:
                # If Server Content != Last Sync Content:
                #    It means Server updated. We paste it locally.
                #    Update Last Sync Content.
                
                if server_content and server_content != last_sync_content:
                    if server_content != local_content:
                        console.print(f"[dim]Received: {server_content[:20].replace('\n', ' ')}...[/dim]")
                        pyperclip.copy(server_content)
                        local_content = server_content # Update local ref so we don't send it back
                    last_sync_content = server_content
                
                # Case B: Local changed (different from Last Sync)
                elif local_content != last_sync_content:
                    # User copied something new locally.
                    console.print(f"[dim]Sending: {local_content[:20].replace('\n', ' ')}...[/dim]")
                    if client.send_clipboard(local_content):
                        last_sync_content = local_content

            except Exception as e:
                # console.print(f"[red]Sync error: {e}[/red]")
                pass
            
            time.sleep(0.5) # Poll faster (0.5s)
            
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
