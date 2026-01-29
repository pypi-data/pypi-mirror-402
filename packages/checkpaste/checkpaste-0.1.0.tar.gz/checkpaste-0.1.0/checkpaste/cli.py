import typer
import uvicorn
import pyperclip
from rich.console import Console
from rich.panel import Panel
from checkpaste.server import app
from checkpaste.client import CheckpasteClient
from checkpaste.utils import get_local_ip

console = Console()
cli = typer.Typer()

@cli.command()
def serve(
    port: int = typer.Option(8000, help="Port to serve on"),
    host: str = typer.Option("0.0.0.0", help="Host interface to bind to")
):
    """
    Start the checkpaste server to receive clipboard text and files.
    """
    local_ip = get_local_ip()
    console.print(Panel(f"[bold green]checkpaste Server Running[/bold green]\n\nLoopback: http://127.0.0.1:{port}\nNetwork:  http://{local_ip}:{port}\n\n[yellow]Share this Network IP with other devices to connect.[/yellow]"))
    uvicorn.run(app, host=host, port=port)

@cli.command()
def copy(
    text: str = typer.Argument(None, help="Text to send. If not provided, reads from local clipboard."),
    host: str = typer.Option("127.0.0.1", help="Host IP of the checkpaste server"),
    port: int = typer.Option(8000, help="Port of the checkpaste server")
):
    """
    Send text to the checkpaste server. If no text is provided, sends current clipboard content.
    """
    if text is None:
        text = pyperclip.paste()
        if not text:
            console.print("[red]Clipboard is empty and no text provided.[/red]")
            return

    client = CheckpasteClient(host, port)
    if client.send_clipboard(text):
        console.print(f"[green]Successfully sent text to {host}:{port}[/green]")
    else:
        console.print("[red]Failed to send text.[/red]")

@cli.command()
def paste(
    host: str = typer.Option("127.0.0.1", help="Host IP of the checkpaste server"),
    port: int = typer.Option(8000, help="Port of the checkpaste server")
):
    """
    Retrieve text from the checkpaste server and copy it to the local clipboard.
    """
    client = CheckpasteClient(host, port)
    text = client.get_clipboard()
    if text:
        pyperclip.copy(text)
        console.print(f"[green]fetched text from {host}:{port} and copied to clipboard![/green]")
        console.print(f"[dim]Content: {text}[/dim]")
    else:
        console.print("[red]Failed to fetch clipboard content.[/red]")

@cli.command()
def send_file(
    file_path: str = typer.Argument(..., help="Path to the file to send"),
    host: str = typer.Option("127.0.0.1", help="Host IP of the checkpaste server"),
    port: int = typer.Option(8000, help="Port of the checkpaste server")
):
    """
    Send a file to the checkpaste server.
    """
    client = CheckpasteClient(host, port)
    if client.send_file(file_path):
        console.print(f"[green]Successfully sent file '{file_path}' to {host}:{port}[/green]")
    else:
        console.print("[red]Failed to send file.[/red]")

def app():
    cli()

if __name__ == "__main__":
    app()
