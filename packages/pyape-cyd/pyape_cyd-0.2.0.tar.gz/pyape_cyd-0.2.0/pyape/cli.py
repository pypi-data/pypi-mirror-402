import functools
import hashlib
import os
from dataclasses import dataclass

import typer
from rich import print

from pyape import Ape, Md5, Sha256, __version__

app = typer.Typer(help="PyApe CLI - Interact with the Gorille Server REST API (APE)")

def compute_md5(filepath: str) -> Md5:
    """Compute and return MD5 hash of a file."""
    hasher_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher_md5.update(chunk)
    return Md5(hasher_md5.hexdigest())


def compute_sha256(filepath: str) -> Sha256:
    """Compute and return SHA256 hash of a file."""
    hasher_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher_sha256.update(chunk)
    return Sha256(hasher_sha256.hexdigest())


@dataclass
class AppContext:
    ape: Ape

def version_callback(value: bool):
    if value:
        print(f"PyApe version: {__version__}")
        raise typer.Exit()


# Add global options for host and port
@app.callback()
def callback(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show PyApe version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    url: str = typer.Option("http://localhost/api", help="APE URL"),
    username: str = typer.Option("user", help="APE username"),
    password: str = typer.Option("user", help="APE password"),
    apikey: str = typer.Option(None, help="APE API key (only if you don't use username/password auth method)"),
):
    """Create APE instance
    """
    ape= Ape(
        url=url,
        username=username,
        password=password,
        apikey=apikey,
    )
    ctx.obj = AppContext(ape=ape)

def ape_command_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # context: AppContext = kwargs['ctx'].obj
        r = func(*args, **kwargs)
        print(r.model_dump_json(indent=4, exclude_unset=True))

    return wrapper

@app.command()
@ape_command_wrapper
def static(
    ctx: typer.Context,
    filepath_or_filehash_or_fileid: str,
    force: bool = typer.Option(False),
    details: bool = typer.Option(False),
    early_exit: bool = typer.Option(False),
    extract: bool = typer.Option(True),
    password: str | None = typer.Option(None),
):
    """Perfrom a static analysis (by file path, file hash or file ID)."""
    context: AppContext = ctx.obj

    # Check if file is a filepath or a hash
    if os.path.exists(filepath_or_filehash_or_fileid):
        return context.ape.post_file_by_upload(
            filepath_or_filehash_or_fileid,
            "/static",
            force,
            details,
            extract,
            early_exit,
            password
        )
    else:
        # Else assume this is a file hash or a file ID
        return context.ape.post_file_by_id(
            filepath_or_filehash_or_fileid,
            "/static",
            force,
            details,
            extract,
            early_exit,
            password
        )

@app.command()
@ape_command_wrapper
def dynamic(
    ctx: typer.Context,
    filepath_or_filehash_or_fileid: str,
    force: bool = typer.Option(False),
    details: bool = typer.Option(False),
    early_exit: bool = typer.Option(False),
    extract: bool = typer.Option(True),
    password: str | None = typer.Option(None),
):
    """Perfrom a dynamic analysis (by file path, file hash or file ID)."""
    context: AppContext = ctx.obj

    # Check if file is a filepath or a hash
    if os.path.exists(filepath_or_filehash_or_fileid):
        return context.ape.post_file_by_upload(
            filepath_or_filehash_or_fileid,
            "/dynamic",
            force,
            details,
            extract,
            early_exit,
            password
        )
    else:
        # Else assume this is a file hash or a file ID
        return context.ape.post_file_by_id(
            filepath_or_filehash_or_fileid,
            "/dynamic",
            force,
            details,
            extract,
            early_exit,
            password
        )


@app.command()
@ape_command_wrapper
def auto(
    ctx: typer.Context,
    filepath_or_filehash_or_fileid: str,
    force: bool = typer.Option(False),
    details: bool = typer.Option(False),
    early_exit: bool = typer.Option(False),
    extract: bool = typer.Option(True),
    password: str | None = typer.Option(None),
):
    """Perfrom an automatic analysis (by file path, file hash or file ID)."""
    context: AppContext = ctx.obj

    # Check if file is a filepath or a hash
    if os.path.exists(filepath_or_filehash_or_fileid):
        return context.ape.post_file_by_upload(
            filepath_or_filehash_or_fileid,
            "/auto",
            force,
            details,
            extract,
            early_exit,
            password
        )
    else:
        # Else assume this is a file hash or a file ID
        return context.ape.post_file_by_id(
            filepath_or_filehash_or_fileid,
            "/auto",
            force,
            details,
            extract,
            early_exit,
            password
        )

@app.command()
@ape_command_wrapper
def get_file(
    ctx: typer.Context,
    filepath_or_filehash_or_fileid: str,
    details: bool = typer.Option(False),
):
    """Get a file analysis (by file path, file hash or file ID)."""
    context: AppContext = ctx.obj

    if os.path.exists(filepath_or_filehash_or_fileid):
        file_md5 = compute_md5(filepath_or_filehash_or_fileid)
        return context.ape.get_file(file_md5, "", details)
    else:
        # Else assume this is a file hash or a file ID
        return context.ape.get_file(filepath_or_filehash_or_fileid, "", details)


@app.command()
@ape_command_wrapper
def get_analysis(
    ctx: typer.Context,
    file_id: str,
    analysis_engine: str,
):
    """Get a specific analysis of file analysis (e.g. magic)."""
    context: AppContext = ctx.obj

    return context.ape.get_file_analysis(file_id, analysis_engine)



@app.command()
@ape_command_wrapper
def about(
    ctx: typer.Context
):
    """Send a GET on /v2/about."""
    context: AppContext = ctx.obj
    r = context.ape.about()
    return r


def main():
    app()

if __name__ == "__main__":
    main()

