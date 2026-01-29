# Typer CLI implementation
import asyncio
import re
import logging as log
import typer
from typing import Optional, List
from pybibget.bibentry import Bibget
from pybtex.database import parse_string

log.getLogger("asyncio").setLevel(log.WARNING)

get_app = typer.Typer()
parse_app = typer.Typer()
update_app = typer.Typer()
app = typer.Typer(name="pybib")


def get_citations(keys, verbose=log.WARNING, interactive=True, file=None):
    """
    Retrieves BibTeX entries for given citation keys and writes them to file or stdout
    """
    log.basicConfig(format="%(levelname)s: %(message)s", level=verbose)
    if not interactive:
        log.info("Running in non-interactive mode")
    bibget = Bibget(mathscinet=True, interactive=interactive)
    bib_data = asyncio.run(bibget.citations(keys))
    number_of_entries = len(bib_data.entries)
    bib_data = bib_data.to_string("bibtex")
    if file:
        with open(file, "a") as obj:
            obj.write(bib_data)
            print(
                f"Successfully appended {number_of_entries} BibTeX entries to {file}."
            )
    else:
        print("\n" + bib_data)
    return number_of_entries


@get_app.command()
def get(
    keys: List[str] = typer.Argument(
        None, help="Citation keys (MRxxxxx, arXiv, PMID, DOI)", metavar="citekeys"
    ),
    file_name: Optional[str] = typer.Option(
        None, "-w", help="Append output to file (default: stdout)"
    ),
    arxiv_author: Optional[str] = typer.Option(
        None, "-arxiv", help="Get all articles from an arXiv author identifier"
    ),
    verbose: bool = typer.Option(False, help="Verbose output"),
    debug: bool = typer.Option(False, help="Debug output"),
    interactive: bool = typer.Option(True, help="Ask for interactive input"),
):
    """Retrieve BibTeX citations from MathSciNet, arXiv, PubMed, DOI."""

    all_keys = list(keys) if keys else []
    if arxiv_author:
        bibget = Bibget(mathscinet=True)
        all_keys += asyncio.run(bibget.arxiv_list(arxiv_author))
    if not all_keys:
        typer.echo("No citation keys provided.")
        raise typer.Exit(code=1)
    get_citations(
        all_keys,
        interactive=interactive,
        file=file_name,
        verbose=log.DEBUG if debug else log.INFO if verbose else log.WARNING,
    )


@parse_app.command()
def parse(
    file_name: str = typer.Argument(
        ..., help="LaTeX file to be parsed for missing citations", metavar="tex_file"
    ),
    write: Optional[str] = typer.Option(
        None, "-w", help="Append output to file (default: stdout)"
    ),
    verbose: bool = typer.Option(False, help="Verbose output"),
    debug: bool = typer.Option(False, help="Debug output"),
    interactive: bool = typer.Option(True, help="Ask for interactive input"),
):
    """Parse .blg file for missing citations and retrieve them."""
    if file_name.endswith(".tex"):
        base_file_name = file_name[:-4]
    else:
        base_file_name = file_name
    try:
        with open(base_file_name + ".blg") as file:
            blg_file = file.read()
    except FileNotFoundError:
        typer.echo(f"BLG file not found: {base_file_name}.blg")
        raise typer.Exit(code=1)
    missing_cites = re.findall(
        r"I didn't find a database entry for '([A-Za-z0-9\.-_ :\/]*)'", blg_file
    )
    missing_cites += re.findall(
        r'I didn\'t find a database entry for "([A-Za-z0-9\.-_ :\/]*)"', blg_file
    )
    bib_file_names = (
        re.findall(r"Found BibTeX data source '([A-Za-z0-9.\-_\/]*)'", blg_file)
        + re.findall(r"Looking for bibtex file '([A-Za-z0-9.\-_\/]*)'", blg_file)
        + re.findall(r"Database file #\d: ([A-Za-z0-9.\-_\/]*)\n", blg_file)
        + re.findall(r"I couldn\'t open database file ([A-Za-z0-9.\-_\/]*)\n", blg_file)
    )
    if missing_cites:
        if write:
            if not bib_file_names and write == " ":
                typer.echo(
                    "No .bib file found. Please specify the .bib file via '-w file_name.bib'"
                )
                raise typer.Exit(code=1)
            file_name = bib_file_names[0] if write == " " else write
        else:
            file_name = None
        get_citations(
            missing_cites,
            interactive=interactive,
            verbose=log.DEBUG if debug else log.INFO if verbose else log.WARNING,
            file=file_name,
        )
    else:
        typer.echo(
            "No missing citations found. Make sure biber/bibtex is run successfully before running pybib."
        )


@update_app.command()
def update(
    file_name: str = typer.Argument(
        ..., help="Bib file to be parsed for citations", metavar="bib_file"
    ),
    interactive: bool = typer.Option(True, help="Ask for interactive input"),
):
    """Update BibTeX citations from MathSciNet and Scopus."""
    if not file_name.endswith(".bib"):
        file_name += ".bib"
    try:
        with open(file_name) as file:
            bib_file = file.read()
    except FileNotFoundError:
        typer.echo(f"Bib file not found: {file_name}")
        raise typer.Exit(code=1)
    bibliography = parse_string(bib_file, "bibtex").entries
    bibget = Bibget(mathscinet=True, interactive=interactive)
    updated_bibliography = asyncio.run(bibget.update_all(bibliography))
    with open(file_name, "w") as file:
        file.write(updated_bibliography.to_string("bibtex"))
        typer.echo(f"Wrote the updated bibliography to {file_name}.")


app.add_typer(get_app)
app.add_typer(parse_app)
app.add_typer(update_app)

if __name__ == "__main__":
    app()
