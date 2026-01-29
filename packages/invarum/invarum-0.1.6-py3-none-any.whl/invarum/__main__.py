# invarum-cli/invarum/__main__.py
from .main import app

if __name__ == "__main__":
    # This enables "python -m invarum"
    app(prog_name="invarum")