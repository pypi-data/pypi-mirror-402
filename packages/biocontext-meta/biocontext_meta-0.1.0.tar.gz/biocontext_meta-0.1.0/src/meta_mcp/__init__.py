from importlib.metadata import version

from meta_mcp.main import run_app

__version__ = version("biocontext-meta")

__all__ = ["run_app", "__version__"]


if __name__ == "__main__":
    run_app()
