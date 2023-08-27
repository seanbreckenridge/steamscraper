import json
from time import sleep
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import click
import bs4  # type: ignore[import]
from logzero import logger  # type: ignore[import]
from selenium import webdriver  # type: ignore[import]
from selenium.webdriver.remote.webdriver import WebDriver  # type: ignore[import]
from selenium.webdriver.support import expected_conditions as EC  # type: ignore[import]
from selenium.webdriver.common.by import By  # type: ignore[import]
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import]

GAMES_URL = "https://steamcommunity.com/id/{}/games?tab=all"


def is_achievement_url(url: str) -> bool:
    query = urlparse(url).query
    return "achievement" in query


def scrape_game_data(
    username: str, driver: WebDriver, request_all: bool
) -> Dict[str, Any]:
    driver.get(GAMES_URL.format(username))
    sleep(5)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".Panel.Focusable"))
    )

    data = {}

    page_data: str = driver.page_source
    data["main_page"] = page_data
    data["ach"] = {}
    page_soup = bs4.BeautifulSoup(driver.page_source, "html.parser")

    achievement_urls = set()
    # parse URLs for destination pages
    for u in page_soup.find_all("a"):
        url = u["href"]
        if url.startswith(f"https://steamcommunity.com/id/{username}/stats"):
            # achievements
            if is_achievement_url(url):
                if url in achievement_urls:
                    continue
                logger.debug(f"Adding achievement url: {url}")
                achievement_urls.add(url)

        if request_all:
            # check if it is the app/based url
            if url.startswith("https://store.steampowered.com/app"):
                logger.debug(
                    f"Found app url, trying to convert to achievements page: {url}"
                )
                game_parts: List[str] = url.split("/")
                last = game_parts[-1]
                if last.strip() and last.isnumeric():
                    # convert to achievements page
                    stats_url = f"https://steamcommunity.com/id/{username}/stats/{last}/?tab=achievements"

                    if is_achievement_url(stats_url):
                        if stats_url in achievement_urls:
                            continue
                        logger.debug(f"Adding converted achievement url: {stats_url}")
                        achievement_urls.add(stats_url)

    for u in achievement_urls:
        driver.get(u)
        sleep(3)

        # if we redirected to the main page, dont save it
        if f"{username}/stats" not in driver.current_url:
            logger.warning(f"Redirected to main page, skipping {u}")
            continue

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "achieveRow"))
            )
        except Exception as e:
            logger.exception(e)
            logger.warning(
                f"Couldn't find a 'achieveRow' item on {u}, storing page anyways..."
            )
        logger.debug(f"storing page source for {u}")
        data["ach"][u] = str(driver.page_source)

    return data


def login(username, driver):
    driver.get(GAMES_URL.format(username))
    click.secho(
        "Sign in to steam, hit enter when youre done... > ", nl=False, fg="green"
    )
    input()


@click.command()
@click.argument("STEAM_USERNAME")
@click.option(
    "--to-file",
    type=click.Path(),
    required=True,
    help="File to store HTML dumps to",
)
@click.option(
    "--chromedriver-path",
    type=click.Path(exists=True),
    required=False,
    help="Location of the chromedriver",
)
@click.option(
    "--request-all",
    is_flag=True,
    help="Request all pages, not just ones with achievements. This is useful if you want data from all games, or the main page hasnt updated some achievements yet.",
    default=False,
)
def main(
    steam_username: str,
    to_file: str,
    chromedriver_path: Optional[str],
    request_all: bool,
) -> None:
    options = webdriver.ChromeOptions()
    if chromedriver_path:
        options.binary_location = chromedriver_path

    driver = webdriver.Chrome(options=options)

    try:
        login(steam_username, driver)
        game_data = scrape_game_data(steam_username, driver, request_all)
    except Exception as e:
        logger.exception(e)
        return
    finally:
        driver.quit()

    with open(to_file, "w") as to_f:
        json.dump(game_data, to_f)


if __name__ == "__main__":
    main()
