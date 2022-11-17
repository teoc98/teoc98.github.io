##    Copyright (C) 2021  Matteo Cavallaro
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU Affero General Public License as
##    published by the Free Software Foundation, either version 3 of the
##    License, or (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU Affero General Public License for more details.
##
##    You should have received a copy of the GNU Affero General Public License
##    along with this program.  If not, see <https://www.gnu.org/licenses/>.

##    https://matteo.ga/triestenext

from bs4 import BeautifulSoup, Tag
from dateparser import DateDataParser
from ics import Calendar, Event, Organizer
import os.path
import requests
import sys
from tqdm import tqdm

## Cache http responses
def get_page(url, update=False):
    file = url.replace("_", "__").replace("/", "_\\")
    file = os.path.join(PAGE_DIR, file)
    if (
        not update
        and os.path.exists(file)
        and (os.path.isfile(file) or os.path.islink(file))
    ):
        with open(file, "r") as f:
            html = f.read()
    else:
        r = requests.get(url)
        html = r.text
        with open(file, "w") as f:
            f.write(html)
    return html


URL = "https://www.triestenext.it/programma"
PAGE_DIR = "./pages"
CALENDAR_PRODID = "-//matteo.ga//Triest Next 2021/IT"
CALENDAR_URL = "https://matteo.ga/triestenext/triestenext21.ics"
CALENDAR_NAME = "Trieste Next 2021"

update = False

soup = BeautifulSoup(get_page(URL, update), features="lxml")
events_div = soup.find("div", class_="col-md-12")
event_divs = events_div.find_all("div", class_="event-item row")

ddp = DateDataParser(
    ["it", "en"], settings={"TIMEZONE": "Europe/Rome", "TO_TIMEZONE": "UTC"}
)
calendar = Calendar()
calendar.events = []
organizer = Organizer("info@goodnet.it", "Triste Next")
for e in tqdm(event_divs, unit="event"):
    info = e.find("div", class_="col-md-4").find("div", class_="side-content")

    ## Parse date and time
    date_div = info.find("div", class_="date")
    date_div_children = list(date_div.children)
    date_text = date_div_children[0].strip()
    date, time = map(str.strip, date_text.split("/"))
    time_starting, time_ending = map(str.strip, time.replace("ore", "").split("-"))
    location = date_div_children[2].strip()
    begin, end = (
        ddp.get_date_data(f"{date} {time}") for time in (time_starting, time_ending)
    )

    ## Retrieve section
    sezione_div = e.find("div", class_="sezione-programma")
    sezione = sezione_div.a.text if sezione_div != None else None
    a = info.find("a")
    title = a.text
    link = a["href"]

    ## Make description (including section)
    soup2 = BeautifulSoup(get_page(link, update), features="lxml")
    main = soup2.find("main")
    description = ["Sezione", sezione] if sezione != None else []
    for e in main.children:
        if isinstance(e, Tag):
            class_ = e["class"][0]
            if class_ in ["date", "title", "sezione-programma", "event-actions"]:
                pass
            elif class_ == "relatori":
                divs = e.find_all("div")
                for d in divs:
                    if not any(
                        isinstance(ee, Tag) and ee.name == "div" for ee in d.children
                    ):
                        text = d.text.strip()
                        if d["class"][0] == "etichetta-realtore":
                            text = "\n" + text
                        description.append(text)
                    description.append("")
            elif class_ in ["testo-evento", "etichetta-realtore", "note"]:
                text = e.text.strip()
                description.append(e.text.strip() + "\n")
            else:
                print(f"Unknown div class '{class_}'", file=sys.stderr)
    description.append(f"Link: {link}")
    description = "\n".join(description)

    event = Event(
        name=title,
        begin=begin.date_obj,
        end=end.date_obj,
        description=description,
        location=location,
        url=link,
        organizer=organizer,
    )
    calendar.events.append(event)

ics_lines = list(calendar)
i = next(iter(i for i, line in enumerate(ics_lines) if line.startswith("PRODID")))

ics_lines = (
    ics_lines[:i]
    + [
        f"PRODID:{CALENDAR_PRODID}\n",
        f"NAME:{CALENDAR_NAME}\n",
        f"X-WR-CALNAME:{CALENDAR_NAME}\n",
    ]
    + ics_lines[i + 1 :]
)

print(*ics_lines, sep="")
