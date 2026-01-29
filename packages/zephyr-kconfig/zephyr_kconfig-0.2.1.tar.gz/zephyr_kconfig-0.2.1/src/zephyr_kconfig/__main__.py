import logging
import sys
from typing import Annotated, Any, cast

import typer
from rich import print as rprint
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from typer import Typer

from zephyr_kconfig import __version__
from zephyr_kconfig._locations import cache_directory
from zephyr_kconfig._types import CmdState

from ._doc_loaders import from_release
from ._models import KConfigDoc, KConfigDocItem

_LOGGER = logging.getLogger(__name__)

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


cli_app = Typer(name=f"Zephyr KConfig Client [{__version__}]")


@cli_app.callback()
def main(
    ctx: typer.Context,
    release: Annotated[
        str,
        typer.Option(
            help="Zephyr release name (Only 4.1 and above are supported) e.g. 4.3.0, 4.2.0, 4.1.0, latest",
        ),
    ],
    loglevel: Annotated[
        str,
        typer.Option(
            "--loglevel",
            "-l",
            help="Set the logging level (debug, info, warning, error, critical)",
        ),
    ] = "warning",
    cache: Annotated[bool, typer.Option(help="Whether to cache the kconfig.json file for future use")] = True,
) -> None:
    logging.basicConfig(level=LOG_LEVELS.get(loglevel, logging.WARNING))
    logging.getLogger("zephyr_kconfig").setLevel(LOG_LEVELS.get(loglevel, logging.WARNING))

    if release != "latest":
        major, minor, _ = map(int, release.split("."))

        if major != 4 or minor < 1:
            typer.echo("Unsupported Zephyr release. Only 4.1 and above are supported.")
            sys.exit(1)

    # cache file_name
    file_name = cache_directory().joinpath(f"kconfig-{release}.json")

    if file_name.exists() and cache:
        _LOGGER.info(f"Loading kconfig.json for release {release} from cache ...")
        kconfig_doc = KConfigDoc.model_validate_json(file_name.read_text())
    else:
        kconfig_doc = from_release(release)
        # save the kconfig_doc to cache for future use
        file_name.write_text(kconfig_doc.model_dump_json())

    ctx.ensure_object(CmdState)
    ctx.obj = CmdState()
    ctx.obj.doc = kconfig_doc


@cli_app.command()
def get(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="The CONFIG_XX to get")],
    exact: Annotated[bool, typer.Option(help="Whether to match the name exactly")] = False,
    indent: Annotated[int, typer.Option(help="Number of spaces to indent the JSON output, -1 to have no indent")] = 2,
    metadata: Annotated[bool, typer.Option(help="Whether to include metadata fields in the output")] = False,
) -> None:
    """Print the CONFIG_XX symbol entries as json output"""

    state = cast(CmdState, ctx.obj)

    config_items = state.doc.get_symbols(name, exact=exact)

    doc = KConfigDoc(
        gh_base_url=state.doc.gh_base_url,
        zephyr_version=state.doc.zephyr_version,
        symbols=config_items,
    ).model_dump_json(
        indent=indent if indent >= 0 else None,
        include={"gh_base_url", "zephyr_version", "symbols"},
        exclude={"symbols": {"__all__": {"filename", "linenr", "menupath"}}} if metadata is False else {},
        exclude_defaults=True,
        exclude_none=True,
    )

    sys.stdout.write(doc)


@cli_app.command()
def deps(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="The CONFIG_XX whose dependencies to get")],
) -> None:
    """Print the dependencies string of CONFIG_XX symbol [Must pass an exact name]"""

    state = cast(CmdState, ctx.obj)

    config_items = state.doc.get_symbols(name, exact=True)

    # Note-
    # [Check] Some CONFIG_XX symbols may have multiple entries (e.g. if defined in multiple Kconfig files)
    # Hence it is an array. This needs revisit.

    if len(config_items) == 0:
        sys.stderr.write(f"Error: Symbol {name} not found in KConfig or is not exact.\n")
        return

    for c in config_items:
        if c.dependencies:
            sys.stdout.write(f"{c.dependencies}\n")
        else:
            sys.stdout.write(f"No dependencies for {c.name}\n")


@cli_app.command()
def pprint(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="The CONFIG_XX to describe")],
    exact: Annotated[bool, typer.Option(help="Whether to match the name exactly")] = False,
) -> None:
    """Pretty print the details about CONFIG_XXX symbol(s)"""

    state = cast(CmdState, ctx.obj)

    config_items = state.doc.get_symbols(name, exact=exact)

    if not config_items:
        rprint(f"[red]Error: Symbol {name} not found in KConfig document.[/red]")
        return

    console = Console()

    def _make_table(column_name: str, items: list[str]) -> Table:
        """Make a simple table with items."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(column_name, style="white")
        for item in items:
            table.add_row(item)
        return table

    def _display_config_item(console: Console, config_item: KConfigDocItem) -> None:
        """Display a single KConfig item with its properties."""

        # Create main info table
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")

        if config_item.prompt:
            info_table.add_row("Prompt", config_item.prompt)
        info_table.add_row("Type", config_item.type or "N/A")
        info_table.add_row("Dependencies", config_item.dependencies)

        defaults_table = _make_table("Defaults", config_item.defaults) if config_item.defaults else None
        selects_table = _make_table("Selects", config_item.selects) if config_item.selects else None
        implies_table = _make_table("Implies", config_item.implies) if config_item.implies else None
        selected_by_table = _make_table("Selected By", config_item.selected_by) if config_item.selected_by else None
        implied_by_table = _make_table("Implied By", config_item.implied_by) if config_item.implied_by else None
        choices_table = _make_table("Choices", config_item.choices) if config_item.choices else None

        items: list[Any] = []
        if config_item.help:
            items.append(
                Panel(
                    config_item.help,
                    title="Description",
                    border_style="blue",
                )
            )
        if defaults_table:
            items.append(defaults_table)
        if selects_table:
            items.append(selects_table)
        if implies_table:
            items.append(implies_table)
        if selected_by_table:
            items.append(selected_by_table)
        if implied_by_table:
            items.append(implied_by_table)
        if choices_table:
            items.append(choices_table)

        panel_group = Group(info_table, *items)

        console.print(Panel(panel_group, title=f"{config_item.name}", border_style="green"), markup=False)

    for item in config_items:
        _display_config_item(console, item)
