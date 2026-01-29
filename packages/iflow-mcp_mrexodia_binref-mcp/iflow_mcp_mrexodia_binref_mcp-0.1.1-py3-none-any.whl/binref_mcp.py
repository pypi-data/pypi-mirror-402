import os
import sys
import argparse
import subprocess
from urllib.parse import urlparse
from zeromcp import McpServer

mcp = McpServer("binref")

# NOTE: this is not secure
os.environ["PATH"] = os.path.dirname(sys.executable)


@mcp.tool
def binref_cmd(command: str) -> str:
    """
    Execute a binref shell command and return the output.
    You can get help by running `binref -h`
    """
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True, encoding="utf-8"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


def main():
    parser = argparse.ArgumentParser(description="MCP Example Server")
    parser.add_argument(
        "--transport",
        help="Transport (stdio or http://host:port)",
        default="http://127.0.0.1:5001",
    )
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.stdio()
    else:
        url = urlparse(args.transport)
        if url.hostname is None or url.port is None:
            raise Exception(f"Invalid transport URL: {args.transport}")

        mcp.serve(url.hostname, url.port)

        try:
            input("\nServer is running, press Enter or Ctrl+C to stop...")
        except (KeyboardInterrupt, EOFError):
            print("\n\nStopping server...")
            mcp.stop()


if __name__ == "__main__":
    main()