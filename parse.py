import json
from urllib.parse import urlparse

import click
from logzero import logger
from bs4 import BeautifulSoup as soup

@click.command()
@click.option(
    "--from-file",
    type=click.Path(exists=True),
    required=True,
    help="File that contains the HTML dumps",
)
@click.option(
    "--to-file",
    type=click.Path(),
    required=True,
    help="File to store parsed JSON to",
)
def main(from_file: str, to_file: str):
    with open(from_file, 'r') as fj:
        raw_data = json.load(fj)

    parsed_data = {}

    import IPython
    IPython.embed()


if __name__ == "__main__":
    main()
