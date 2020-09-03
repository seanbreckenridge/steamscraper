# steamscraper

Scrapes game/achievement data from steams website.

Doesn't seem to be a simple way to download the data using the GDPR site, this is a thrown together `selenium` implementation. Assumes you have [`selenium`](https://selenium-python.readthedocs.io/) setup.

I'm not sure if some of these pages are paginated or not, I don't use steam that actively. It seems to be all of the data though.

Saves:

- image URL
- hours on record
- achievements

To minimize pain and suffering resulting from webscrapings, `scrape.py` is as generic as possible when scraping, and saves the entire HTML contents of the pages. Then `extract` tries to parse that into the values I want.

---

Requires `python3.7+`

```
git clone https://github.com/seanbreckenridge/steamscraper
cd steamscraper
pip install -r ./requirements.txt
# username is the one that works here: https://steamcommunity.com/id/<steam_username>/games?tab=all
python3 ./scrape.py <steam_username> --to-file ./data.json
python3 ./parse.py --from-file ./data.json --to-file ./parsed.json
python3 ./demo.py --from-file  ./parsed.json
```

---

In `parsed.json`, each contains how many hours, the image, and achievement data/when you earned the achievements.

Dates are serialized to epoch time, if possible.

`{"730": {"id": 730, "name": "Counter-Strike: Global Offensive", "hours": 154.0, "image": "https://steamcdn-a.akamaihd.net/steam/apps/730/capsule_184x69.jpg", "achievements": [{"icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/730/9f60ea3c56b4ab248ab598bbd62568b953116301.jpg", "title": "Someone Set Up Us The Bomb", "description": "Win a round by planting a bomb", "progress": {"unlocked": true, "data": 1454391360}}, {"icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/730/b11ef0453168cd3d10684e184004f71dcc0faa82.jpg", "title": "Body Bagger", "description": "Kill 25 enemies",`

---

Demo Output:

```
+---------------------------+-------+-------------+---------+
|            Name           | Hours | Achivements | Most In |
+---------------------------+-------+-------------+---------+
|   Counter-Strike: Global  | 154.0 |    79/167   |   2016  |
|         Offensive         |       |             |         |
|       Rocket League       | 102.0 |    36/88    |   2016  |
|    RWBY: Grimm Eclipse    |  23.0 |    26/37    |   2017  |
|      Team Fortress 2      |  22.0 |    14/520   |   2014  |
|  Crypt of the NecroDancer |  13.8 |     2/44    |   2016  |
|      Life is Strange™     |  13.3 |     9/60    |   2017  |
|         Undertale         |  11.5 |     0/0     |   ----  |
|  VA-11 Hall-A: Cyberpunk  |  10.1 |    19/34    |   2018  |
|      Bartender Action     |       |             |         |
|       Papers, Please      |  5.6  |     2/9     |   2017  |
|       Hotline Miami       |  5.2  |     8/27    |   2018  |
|     Spec Ops: The Line    |  4.9  |    28/50    |   2018  |
|         Broken Age        |  4.4  |    10/39    |   2016  |
|         Transistor        |  4.0  |     9/33    |   2017  |
+---------------------------+-------+-------------+---------+
```
