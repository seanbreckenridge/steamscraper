# steamscraper

Scrapes game data from the [GDPR portal](https://help.steampowered.com/en/accountdata) on steams website.

Doesn't seem to be a simple way to download the data from the site, this is a thrown together `selenium` implementation. Assumes you have [`selenium`](https://selenium-python.readthedocs.io/) setup.

I'm not sure if some of these are paginated or not, I don't use steam that actively.

Saves:

- Game Data
    - hours on record
    - achievements, if any
    - personal game data, if any

To minimize pain and suffering resulting from webscrapings, `scrape.py` is as generic as possible when scraping, and saves the entire HTML contents of the pages. Then `extract` tries to parse that into JSON

## Installation

Requires `python3.7+`

```
git clone https://github.com/seanbreckenridge/steamscraper
cd steamscraper
pip install -r ./requirements.txt
python3 ./scrape.py <username> --to ./data.json
python3 ./parse.py --from-file ./data.json --to-file ./parsed.json
```

