"""
ABSFUYU CLI
-----------
Checksum

Version: 6.3.0
Date updated: 21/01/2026 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = ["checksum_group"]


# Library
# ---------------------------------------------------------------------------
from string import Template

import click

from absfuyu.tools.checksum import DirectoryChecksumMixin

verify_output = Template(
    """\
$index. $file
- Status: $status
- Old hash: $old_hash
- New hash: $new_hash
"""
)


# CLI
# ---------------------------------------------------------------------------
@click.command(name="start")
@click.argument("path", type=str)
@click.option(
    "--hashmode",
    "-m",
    "hash_mode",
    type=click.Choice(["md5", "sha1", "sha256", "sha512"]),
    default="sha256",
    show_default=True,
    help="Hash algorithm",
)
@click.option(
    "--save-result",
    "-s",
    "save_result",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Save checksum result to file",
)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Do checksum for every file in the folder (including child folder)",
)
@click.option(
    "--multithread",
    "-x",
    "multithreaded",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Run in multithreaded mode",
)
def new_checksum(
    path: str,
    hash_mode: str,
    save_result: bool,
    recursive_mode: bool,
    multithreaded: bool,
) -> None:
    """Start doing checksum for directory"""
    instance = DirectoryChecksumMixin(path, algorithm=hash_mode, recursive=recursive_mode)
    res = instance.checksum(multithreaded=multithreaded, save_to_db=save_result)

    if res is not None:
        click.echo(res)
    click.echo("Done")


@click.command(name="verify")
@click.argument("path", type=str)
@click.option(
    "--hashmode",
    "-m",
    "hash_mode",
    type=click.Choice(["md5", "sha1", "sha256", "sha512"]),
    default="sha256",
    show_default=True,
    help="Hash algorithm",
)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Verify every file in the folder (including child folder)",
)
@click.option(
    "--multithread",
    "-x",
    "multithreaded",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Run in multithreaded mode",
)
def verify_integrity(path: str, hash_mode: str, recursive_mode: bool, multithreaded: bool) -> None:
    """Verify integrity of files in path (must exists checksum.db)"""
    instance = DirectoryChecksumMixin(path, algorithm=hash_mode, recursive=recursive_mode)
    try:
        res = instance.verify_integrity(multithreaded=multithreaded)
    except Exception:
        click.echo("ERROR: Run checksum and save to file first with -s flag")
        raise SystemExit()

    if res:
        click.echo("Changes")
        for i, x in enumerate(res, start=1):
            v = x.to_dict(instance.source_path)
            click.echo(
                verify_output.safe_substitute(
                    index=f"{i:02}",
                    file=v["path"],
                    status=v["status"].title(),
                    old_hash=v["old"],
                    new_hash=v["new"],
                )
            )
    else:
        click.echo("No changes found!")


@click.command(name="dd")
@click.argument("path", type=str)
@click.option(
    "--dryrun",
    "-d",
    "dry_run",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Simulate deleting only",
)
@click.option(
    "--hashmode",
    "-m",
    "hash_mode",
    type=click.Choice(["md5", "sha1", "sha256", "sha512"]),
    default="sha256",
    show_default=True,
    help="Hash algorithm",
)
@click.option(
    "--recursive",
    "-r",
    "recursive_mode",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Scan every file in the folder (including child folder)",
)
@click.option(
    "--ignore-db",
    "-i",
    "ignore_database",
    type=bool,
    default=False,
    is_flag=True,
    show_default=True,
    help="Delete duplicate files without relying on an existing database",
)
@click.option(
    "--keepmode",
    "-k",
    "keep_mode",
    type=click.Choice(["first", "last", "newest", "oldest"]),
    default="first",
    show_default=True,
    help="Keep mode",
)
def del_dups(
    path: str,
    hash_mode: str,
    recursive_mode: bool,
    dry_run: bool,
    keep_mode: str,
    ignore_database: bool,
) -> None:
    """Delete duplicates by comparing checksum hash value"""
    instance = DirectoryChecksumMixin(path, algorithm=hash_mode, recursive=recursive_mode)
    res = instance.delete_duplicates(dry_run=dry_run, keep=keep_mode, ignore_database=ignore_database)

    if res:
        click.echo("Deleted files")
        for i, x in enumerate(res, start=1):
            click.echo(f"{i:02}. {str(x.relative_to(instance.source_path))}")
    else:
        click.echo("No duplicates found!")


@click.group(name="cs")
def checksum_group() -> None:
    """Checksum tool"""
    pass


checksum_group.add_command(new_checksum)
checksum_group.add_command(verify_integrity)
checksum_group.add_command(del_dups)
