import json
import textwrap
from typing import Optional
from datetime import datetime
from collections import Counter

import click
from prettytable import PrettyTable

tw = textwrap.TextWrapper(width=25, drop_whitespace=True, max_lines=2)

def ach_stats(ach):
    count = 0
    for a in ach:
        if a['progress']['unlocked']:
            count += 1
    return "{}/{}".format(count, len(ach))

def most_achieved_in(ach):
    dates = []
    for a in ach:
        if a['progress']['unlocked']:
            dates.append(datetime.fromtimestamp(a['progress']['data']).year)
    c = Counter(dates)
    if len(c):
        return c.most_common(1)[0][0]
    else:
        return "----"

@click.command()
@click.option(
    "--from-file",
    type=click.Path(exists=True),
    required=True,
    help="File that contains the HTML dumps",
)
def main(from_file: str):
    with open(from_file, "r") as fj:
        parsed_data = json.load(fj)

    p_table = PrettyTable()
    p_table.field_names = ["Name", "Hours", "Achivements", "Most In"]
    for _, game_data in parsed_data.items():
        p_table.add_row(['\n'.join(tw.wrap(game_data['name'])), game_data['hours'], ach_stats(game_data['achievements']),
                         most_achieved_in(game_data['achievements'])])

    print(p_table)


if __name__ == "__main__":
    main()
