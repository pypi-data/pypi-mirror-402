import asyncio
import sys
from checkpaste import cli  # Adjust import as needed

async def main():
    await cli()  # Or whatever the main CLI entrypoint is

if __name__ == "__main__":
    asyncio.run(main())
