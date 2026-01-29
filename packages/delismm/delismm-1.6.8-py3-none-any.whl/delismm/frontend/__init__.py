import os
import subprocess

if __name__ == "__main__":
    port = 5007
    subprocess.call(
        [
            "bokeh",
            "serve",
            "--show",
            f"--port={port}",
            f"--allow-websocket-origin=localhost:{port}",
            f"--allow-websocket-origin=fa-121050:{port}",
            "main",
        ],
        cwd=os.path.dirname(__file__),
    )
