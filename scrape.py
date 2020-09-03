import json
from time import sleep
from typing import Optional, List, Dict, Set
from urllib.parse import urlparse

import click
from logzero import logger
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from bs4 import BeautifulSoup as soup

GAMES_URL = "https://steamcommunity.com/id/{}/games?tab=all"

STATS_BUTTON_TEXT = "View Stats"
GAMEDATA_BUTTON_TEXT = "Personal Game Data"

def is_achivement_url(url: str) -> bool:
    query = urlparse(url).query
    return 'achievement' in query

def scrape_game_data(username, driver):

    driver.get(GAMES_URL.format(username))
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "gameListRow")))

    already_scraped: Set[set] = set()

    data = {}

    page_data: str = driver.page_source
    data["main_page"] = page_data
    data["ach"] = {}
    data["gd"] = {}
    page_soup = soup(driver.page_source, "html.parser")

    achievement_urls = []
    game_data_urls = []
    # parse URLs for destination pages
    for u in page_soup.find_all("a"):
        url = u["href"]
        if url.startswith("https://steamcommunity.com/id/{}/stats".format(username)):
            # achivements
            if is_achivement_url(url):
                achievement_urls.append(url)
        if url.startswith("https://steamcommunity.com/id/{}/gcpd".format(username)):
            # game data
            game_data_urls.append(url)

    for u in achievement_urls:
        driver.get(u)
        sleep(3)
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "achieveRow")))
        except Exception as e:
            logger.exception(e)
            logger.warning("Couldn't find a 'achieveRow' item on {}, storing page anyways...".format(u))
        logger.debug("storing page source for {}".format(u))
        data['ach'][u] = str(driver.page_source)

    for u in game_data_urls:
        driver.get(u)
        sleep(3)
        logger.debug("storing page source for {}".format(u))
        data['gd'][u] = str(driver.page_source)

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
    "--to",
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
def main(steam_username: str, to: str, chromedriver_path: Optional[str]):
    cpath = "chromedriver" if chromedriver_path is None else chromedriver_path
    driver = webdriver.Chrome(executable_path=cpath)

    try:
        login(steam_username, driver)
        game_data = scrape_game_data(steam_username, driver)
    except Exception as e:
        logger.exception(e)
    finally:
        driver.quit()

    with open(to, 'w') as to_f:
        json.dump(game_data, to_f)


if __name__ == "__main__":
    main()
