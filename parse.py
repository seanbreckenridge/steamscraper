import re
import json
from datetime import datetime
from typing import Optional, Union, List, Dict, Any, cast, Tuple

import click
import dateparser
import bs4  # type: ignore[import]
from logzero import logger  # type: ignore[import]

Json = Any


def bs4_parse(page_contents: str) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(page_contents, "html.parser")


current_year = str(datetime.now().year)


def _parse_unlocked_time(date_string: str) -> Union[int, str]:
    # second pattern is if it was unlocked in the current year
    for pattern in [
        "Unlocked (\w+) (\d+), (\d+) @ (.*)$",
        "Unlocked (\w+) (\d+) @ (.*)$",
    ]:
        match_data = re.match(pattern, date_string.strip())
        if match_data is not None and bool(match_data.groups()):
            dt_parts: List[str] = [match_data.group(n) for n in (1, 2, 3)]
            if len(match_data.groups()) > 3:
                dt_parts.append(match_data.group(4))
            else:
                # use current year if there was no year in the description
                dt_parts.append(current_year)
            match_string = " ".join(map(str.strip, dt_parts))
            dt = dateparser.parse(match_string)
            if dt is not None:
                return int(dt.timestamp())
    logger.warning("Could not parse datetime {}".format(date_string))
    return date_string


def _get_opt_img(el: Optional[bs4.element.Tag]) -> Optional[str]:
    if el is None:
        return None
    else:
        return cast(str, el["src"])


def _parse_game_id(game_id: str) -> int:
    return int(game_id.lstrip("game_"))


def _parse_game_time(duration: str) -> float:
    if len(duration) == 0:
        return 0.0
    return float(duration.split(" ")[0])


def _game_page_extract_row_attributes(bs4_el):
    game_id = _parse_game_id(bs4_el["id"])
    game_name: str = bs4_el.find(class_="gameListRowItemName").text.strip()
    game_hours_played: str = bs4_el.find(class_="hours_played").text.strip()
    game_image = _get_opt_img(bs4_el.find(class_="gameListRowLogo").find("img"))
    return game_id, {
        "id": game_id,
        "name": game_name,
        "hours": _parse_game_time(game_hours_played),
        "image": game_image,
    }


def game_page(page_contents):
    """
    Extracts name, hours and image from the main game page
    """
    gsoup = bs4_parse(page_contents)
    games = {}
    for el in gsoup.find_all(class_="gameListRow"):
        game_id, game_data = _game_page_extract_row_attributes(el)
        games[game_id] = game_data
    return games


def achievement_row_parser(
    ach_row: bs4.element.Tag,
    title_selector: str = "h3",
    description_selector: str = "h5",
    unlock_selector: str = "achieveUnlockTime",
    progress_selector: str = "progressText",
    img_el: Optional[str] = None,
) -> Json:
    """
    Handles parsing an achievement row
    Works for both the default (95% of steam pages) and TF2 Custom HTML page
    """
    data: Dict[str, Any] = {}
    if img_el is None:
        data["icon"] = _get_opt_img(ach_row.find("img"))
    else:
        data["icon"] = _get_opt_img(img_el.find("img"))
    data["title"] = ach_row.find(title_selector).text.strip()
    data["description"] = ach_row.find(description_selector).text.strip()

    # try a couple patterns to find what the status of the achievement is
    # item is unlocked, has a datetime
    unlocked = ach_row.find(class_=unlock_selector)
    if unlocked is not None:
        data["progress"] = {
            "unlocked": True,
            "data": _parse_unlocked_time(unlocked.text.strip()),
        }
        return data
    # item is locked, has a progress bar
    progress = ach_row.find(class_=progress_selector)
    if progress is not None:
        data["progress"] = {
            "unlocked": False,
            "data": progress.text.strip(),  # could throw error
        }
        return data
    # no item, is not unlocked
    data["progress"] = {"unlocked": False, "data": None}
    return data


def _default_achievement_page(asoup):
    """
    Parses the default steam achievement page
    Most pages use this
    """
    for ach_row in asoup.find_all(class_="achieveRow"):
        yield achievement_row_parser(ach_row)


def _tf2_achievement_page(asoup):
    """
    Parses the achievement page for Team Fortress 2. Is slightly different/has different
    selectors, but generally has the same structure. The achievement_row_parser can
    handle it with a couple kwarg differences and supplying the img_el
    """
    # on the same level, select both images and elements, and then zip em
    images = asoup.find_all(class_="achieveImgHolder")
    ach_datas = asoup.find_all(class_="achieveTxtHolder")
    assert len(images) == len(ach_datas), "TF2 image count != achievement data"
    for img, dat in zip(images, ach_datas):
        yield achievement_row_parser(
            dat, progress_selector="progressFloatRight", img_el=img
        )


def achievement_page(url: str, page_contents: str) -> Tuple[Optional[int], List[Json]]:
    achievements = []
    asoup = bs4_parse(page_contents)
    gameLogo = asoup.find(class_="gameLogo")
    if gameLogo is None:
        return None, []
    game_id = int(gameLogo.find("a")["href"].split("/")[-1])
    if asoup.find(attrs={"id": "personalAchieve"}) is not None:
        logger.debug(f"Parsing {url} with default achievement page parser...")
        achievements.extend(list(_default_achievement_page(asoup)))
        logger.debug(f"Parsed {len(achievements)} achievements...")
    else:
        # try custom HTML parsers
        if "/stats/TF2/" in url:
            achievements.extend(list(_tf2_achievement_page(asoup)))
            logger.debug(f"Parsed {len(achievements)} achievements from TF2...")
        else:
            logger.warning(f"Couldnt parse {url}...")
    return game_id, achievements


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
def main(from_file: str, to_file: str) -> None:
    with open(from_file, "r") as fj:
        raw_data = json.load(fj)

    # get days played/images
    metadata = game_page(raw_data["main_page"])

    # get achievement data
    achievements = {}
    for ach_url, ach_page_contents in raw_data["ach"].items():
        game_id, achievement_data = achievement_page(ach_url, ach_page_contents)
        if game_id is not None and len(achievement_data) > 0:
            achievements[game_id] = achievement_data

    # merge meta/achievement data
    logger.info(
        "combining game/achievement info (ones that dont match probably dont have achievements)"
    )
    parsed_data = {}
    for game_id, metadata in metadata.items():
        parsed_data[game_id] = metadata
        if game_id in achievements:
            parsed_data[game_id]["achievements"] = achievements.pop(game_id)
        else:
            logger.warning(f"Could not find {game_id} in achievements")
            parsed_data[game_id]["achievements"] = []

    if len(achievements):
        logger.warning(
            f"There are {len(achievements)} achievements left which dont match to game IDs!"
        )
        logger.warning(achievements)

    with open(to_file, "w") as tf:
        json.dump(parsed_data, tf)


if __name__ == "__main__":
    main()
