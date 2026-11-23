"""Content data for "The World in One Day", Sunday 22 November 2026.

Everything in this file is DATA typed from the build spec: story texts,
numbers, colours, coordinates and layout strings.  No code, no logic
about drawing lives here.

Counts shown on the page (stories per region, per topic, the coverage
matrix, the first story of each region) are COMPUTED from STORIES by the
helper functions at the bottom, never typed by hand.
"""

# ---------------------------------------------------------------- colours
# Section 3 of the spec, exact RGB values.
PAPER = (247, 244, 236)
INK = (20, 22, 28)
GREY = (96, 98, 106)
RULE = (205, 199, 186)
RED = (176, 22, 30)
NAVY = (16, 34, 64)
WHITE = (255, 255, 255)
GOLD = (250, 206, 102)

# Dark bar along the bottom of every picture panel (section 3).
PANEL_BAR = (16, 22, 34)
# Source names inside a card's place bar (section 3).
PANEL_SOURCE = (196, 204, 220)
# Background bar under the deck line (section 4).
BACKGROUND_FILL = (234, 230, 220)
# "How the day changed" box (section 5.9).
HOW_CHANGED_FILL = (236, 241, 248)
# "Date check" box (section 5.10).
DATE_CHECK_FILL = (251, 240, 236)
# Map colours (section 8).
MAP_OCEAN = (222, 232, 241)
MAP_LAND = (206, 197, 178)
MAP_EQUATOR = (160, 176, 192)
MAP_OUTLINE = (150, 160, 172)
# Coverage table empty cells and "All" column (section 9).
CELL_EMPTY = (238, 234, 226)
CELL_ALL = (222, 218, 208)

REGION_COLORS = {
    "EUROPE": (34, 88, 166),
    "MIDDLE EAST": (190, 92, 14),
    "ASIA-PACIFIC": (18, 122, 132),
    "AFRICA": (40, 122, 72),
    "AMERICAS": (112, 60, 156),
    "WORLD": (88, 88, 96),
}

REGION_NAMES = {
    "EUROPE": "Europe",
    "MIDDLE EAST": "Middle East",
    "ASIA-PACIFIC": "Asia & Pacific",
    "AFRICA": "Africa",
    "AMERICAS": "Americas",
    "WORLD": "World",
}

# Display order for the coverage table header row (section 9).
REGIONS = ["EUROPE", "MIDDLE EAST", "ASIA-PACIFIC", "AFRICA", "AMERICAS", "WORLD"]

CERTAINTY_COLORS = {
    "CONFIRMED": (24, 122, 64),
    "STATED": (176, 112, 8),
    "UNVERIFIED": (192, 54, 30),
}

# Topic row order for the coverage table (section 5.7).
TOPICS = ["CONFLICT", "POLITICS", "ECONOMY", "DISASTER", "SOCIETY", "SPORT"]

# ---------------------------------------------------------------- topics
# Section 5.7: which topic each field belongs to.
TOPIC_OF_FIELD = {
    "ACCIDENT": "DISASTER",
    "CLIMATE": "POLITICS",
    "COALITION": "POLITICS",
    "CRICKET": "SPORT",
    "CRYPTO": "ECONOMY",
    "DEFENCE": "CONFLICT",
    "DIPLOMACY": "POLITICS",
    "DRUGS": "CONFLICT",
    "EARTHQUAKE": "DISASTER",
    "EDUCATION": "SOCIETY",
    "ELECTIONS": "POLITICS",
    "ENERGY": "ECONOMY",
    "EPIDEMIC": "SOCIETY",
    "FOOTBALL": "SPORT",
    "GAZA": "CONFLICT",
    "HEALTH POLICY": "POLITICS",
    "INDUSTRIAL FIRE": "DISASTER",
    "MARKETS": "ECONOMY",
    "MEMORIAL": "SOCIETY",
    "MOTORSPORT": "SPORT",
    "NAVAL WAR": "CONFLICT",
    "POLLUTION": "SOCIETY",
    "PRESS FREEDOM": "POLITICS",
    "PROTEST": "POLITICS",
    "SECURITY": "CONFLICT",
    "SHIPPING": "CONFLICT",
    "SUDAN WAR": "CONFLICT",
    "TECH & SPEECH": "POLITICS",
    "TENNIS": "SPORT",
    "UKRAINE WAR": "CONFLICT",
    "US POLITICS": "POLITICS",
    "WEATHER": "DISASTER",
    "WEST BANK": "CONFLICT",
}

# ---------------------------------------------------------------- stories
# Sections 5.4, 5.5, 5.6 and 5.8.  Leads 1-3 carry headline, body, place
# bar text, red label, sources, certainty and a picture name.  Cards 4-13
# carry headline, place bar text, red label, sources (shown in the place
# bar), certainty and a picture name.  Briefs 14-42 carry place, the
# what-happened text, source, certainty and map coordinates (story 42 has
# none, so no map dot).  Every story 1-41 also carries its map-pin lon/lat.
STORIES = [
    {
        "number": 1, "region": "WORLD", "field": "CLIMATE",
        "headline": "COP31 ends with no deal on fossil fuels",
        "body": "Longest UN climate summit ever closes without a final text: "
                "the EU and others reject a draft that never names fossil "
                "fuels. Guterres: \u201cdeeply disappointing.\u201d",
        "place": "ANTALYA, T\u00dcRK\u0130YE",
        "label": "NO DEAL",
        "sources": "UN News \u00b7 Reuters \u00b7 NPR",
        "certainty": "CONFIRMED",
        "picture": "cop",
        "lon": 30.7, "lat": 36.9,
    },
    {
        "number": 2, "region": "EUROPE", "field": "UKRAINE WAR",
        "headline": "Russian drone strike flattens Kyiv-area block",
        "body": "Overnight strike collapses a five-storey block in Dymer: "
                "11 dead by night, a woman of 79 pulled out alive. Kyiv "
                "says it stopped 161 of 186 drones.",
        "place": "DYMER, NORTH OF KYIV",
        "label": "11 DEAD",
        "sources": "Ukrainska Pravda \u00b7 AP \u00b7 Kyiv Post",
        "certainty": "CONFIRMED",
        "picture": "dymer",
        "lon": 30.3, "lat": 50.9,
    },
    {
        "number": 3, "region": "AFRICA", "field": "NAVAL WAR",
        "headline": "Russian warship capsizes in a Libyan port",
        "body": "Blasts at 03:00 local; by morning the Russian Navy "
                "corvette Merkury lies capsized, bow above water. Libya "
                "suspects Ukrainian sea drones; no one claims it.",
        "place": "BENGHAZI, LIBYA",
        "label": "CAPSIZED",
        "sources": "AP \u00b7 BBC Verify \u00b7 The Guardian",
        "certainty": "UNVERIFIED",
        "certainty_extra": "WHO STRUCK",
        "picture": "benghazi",
        "lon": 20.1, "lat": 32.1,
    },
    {
        "number": 4, "region": "MIDDLE EAST", "field": "ENERGY",
        "headline": "Fuel shortage and war damage force rolling power cuts across Iran",
        "place": "IRAN",
        "label": "2 HRS",
        "sources": "Tavanir, Rudaw",
        "certainty": "CONFIRMED",
        "picture": "power",
        "lon": 51.4, "lat": 35.7,
    },
    {
        "number": 5, "region": "MIDDLE EAST", "field": "SHIPPING",
        "headline": "UKMTO: a tanker was in an incident with military forces off Chabahar",
        "place": "GULF OF OMAN",
        "label": "UKMTO ALERT",
        "sources": "UKMTO, Euronews",
        "certainty": "STATED",
        "picture": "tanker",
        "lon": 60.6, "lat": 25.3,
    },
    {
        "number": 6, "region": "MIDDLE EAST", "field": "WEST BANK",
        "headline": "Settlers torch Palestinian homes; Israel\u2019s Eisenkot calls it \u201cJewish terror\u201d",
        "place": "WEST BANK",
        "label": "ARSON",
        "sources": "Guardian, ToI",
        "certainty": "CONFIRMED",
        "picture": "westbank",
        "lon": 35.2, "lat": 32.0,
    },
    {
        "number": 7, "region": "AFRICA", "field": "EPIDEMIC",
        "headline": "Fighting stalls Ebola response in Congo; WHO\u2019s Tedros pleads for peace",
        "place": "ITURI, DR CONGO",
        "label": "11,613 IN DRC",
        "sources": "Reuters, WHO",
        "certainty": "CONFIRMED",
        "picture": "ebola",
        "lon": 30.2, "lat": 1.6,
    },
    {
        "number": 8, "region": "AFRICA", "field": "SUDAN WAR",
        "headline": "Overnight drone strikes on Khartoum kill at least 4 and hit a UN site",
        "place": "KHARTOUM",
        "label": "UN SITE HIT",
        "sources": "AFP, Xinhua",
        "certainty": "CONFIRMED",
        "picture": "khartoum",
        "lon": 32.5, "lat": 15.6,
    },
    {
        "number": 9, "region": "EUROPE", "field": "PRESS FREEDOM",
        "headline": "Thousands march in Istanbul for press freedom after police seize S\u00f6zc\u00fc TV",
        "place": "ISTANBUL",
        "label": "THOUSANDS",
        "sources": "DW, AP",
        "certainty": "CONFIRMED",
        "picture": "istanbul",
        "lon": 28.9, "lat": 41.0,
    },
    {
        "number": 10, "region": "ASIA-PACIFIC", "field": "ELECTIONS",
        "headline": "Record turnout in Hong Kong vote for the body that picks the city\u2019s leader",
        "place": "HONG KONG",
        "label": "98.79%",
        "sources": "HK Govt, RTHK",
        "certainty": "CONFIRMED",
        "picture": "hk",
        "lon": 114.2, "lat": 22.3,
    },
    {
        "number": 11, "region": "ASIA-PACIFIC", "field": "EDUCATION",
        "headline": "South Korea\u2019s education minister quits over AI cheating chaos at exams",
        "place": "SEOUL",
        "label": "RESIGNS",
        "sources": "Chosun, Guardian",
        "certainty": "CONFIRMED",
        "picture": "seoul",
        "lon": 127.0, "lat": 37.6,
    },
    {
        "number": 12, "region": "AMERICAS", "field": "US POLITICS",
        "headline": "Foxx concedes; Democrats hit 258 House seats, their most since 1992",
        "place": "WASHINGTON",
        "label": "258 SEATS",
        "sources": "AP, CBS",
        "certainty": "CONFIRMED",
        "picture": "house",
        "lon": -77.0, "lat": 38.9,
    },
    {
        "number": 13, "region": "EUROPE", "field": "TENNIS",
        "headline": "Alcaraz beats world No 1 Zverev to win his first ATP Finals title",
        "place": "TURIN",
        "label": "6-2 7-6",
        "sources": "ATP, ESPN",
        "certainty": "CONFIRMED",
        "picture": "tennis",
        "lon": 7.7, "lat": 45.1,
    },
    {
        "number": 14, "region": "EUROPE", "field": "UKRAINE WAR",
        "place": "Vyshneve", "what": "supermarket hit, 3 killed",
        "source": "Kyiv Indep.", "certainty": "STATED",
        "lon": 30.36, "lat": 50.39,
    },
    {
        "number": 15, "region": "EUROPE", "field": "UKRAINE WAR",
        "place": "Kyiv", "what": "Zelensky: 165 missiles in 7 days",
        "source": "Al Jazeera", "certainty": "STATED",
        "lon": 30.52, "lat": 50.45,
    },
    {
        "number": 16, "region": "EUROPE", "field": "UKRAINE WAR",
        "place": "Krasnodar", "what": "drones hit Rosgvardia HQ",
        "source": "Kyiv Post", "certainty": "UNVERIFIED",
        "lon": 38.98, "lat": 45.04,
    },
    {
        "number": 17, "region": "EUROPE", "field": "UKRAINE WAR",
        "place": "Finland", "what": "Russian ship towed away",
        "source": "Coastguard", "certainty": "CONFIRMED",
        "lon": 25.00, "lat": 60.00,
    },
    {
        "number": 18, "region": "EUROPE", "field": "SECURITY",
        "place": "Kaliningrad", "what": "sirens; Russia: false alarm",
        "source": "ISW", "certainty": "STATED",
        "lon": 20.51, "lat": 54.71,
    },
    {
        "number": 19, "region": "EUROPE", "field": "WEATHER",
        "place": "Paris", "what": "rain-flood warning issued",
        "source": "M\u00e9t\u00e9o-France", "certainty": "CONFIRMED",
        "lon": 2.35, "lat": 48.86,
    },
    {
        "number": 20, "region": "EUROPE", "field": "FOOTBALL",
        "place": "Anfield", "what": "Liverpool 4\u20130 Man United",
        "source": "LFC, Sky", "certainty": "CONFIRMED",
        "lon": -2.96, "lat": 53.43,
    },
    {
        "number": 21, "region": "MIDDLE EAST", "field": "COALITION",
        "place": "Israel", "what": "unity-govt talks: no deal",
        "source": "AJ, Ynet", "certainty": "CONFIRMED",
        "lon": 34.85, "lat": 32.08,
    },
    {
        "number": 22, "region": "MIDDLE EAST", "field": "GAZA",
        "place": "Gaza", "what": "4 killed despite truce",
        "source": "Health Min.", "certainty": "STATED",
        "lon": 34.45, "lat": 31.50,
    },
    {
        "number": 23, "region": "MIDDLE EAST", "field": "DIPLOMACY",
        "place": "Doha", "what": "no imminent US\u2013Iran deal",
        "source": "Jiji", "certainty": "STATED",
        "lon": 51.53, "lat": 25.29,
    },
    {
        "number": 24, "region": "MIDDLE EAST", "field": "DRUGS",
        "place": "Damascus", "what": "400m captagon pills burned",
        "source": "Arabiya", "certainty": "STATED",
        "lon": 36.29, "lat": 33.51,
    },
    {
        "number": 25, "region": "MIDDLE EAST", "field": "SECURITY",
        "place": "Lebanon", "what": "3 held, 264 kg explosives",
        "source": "Arabiya", "certainty": "STATED",
        "lon": 35.50, "lat": 33.89,
    },
    {
        "number": 26, "region": "AFRICA", "field": "ACCIDENT",
        "place": "Nigeria", "what": "funeral-boat toll rises to 24",
        "source": "NEMA", "certainty": "CONFIRMED",
        "lon": 8.00, "lat": 10.00,
    },
    {
        "number": 27, "region": "AFRICA", "field": "SUDAN WAR",
        "place": "Sudan", "what": "RSF commander defects",
        "source": "Ahram", "certainty": "UNVERIFIED",
        "lon": 30.00, "lat": 15.00,
    },
    {
        "number": 28, "region": "AFRICA", "field": "MEMORIAL",
        "place": "S. Africa", "what": "Mlambo-Ngcuka mourned",
        "source": "Presidency", "certainty": "CONFIRMED",
        "lon": 28.19, "lat": -25.75,
    },
    {
        "number": 29, "region": "AFRICA", "field": "ELECTIONS",
        "place": "Kenya", "what": "govt: tally 2027 vote in Nairobi",
        "source": "Dawan", "certainty": "STATED",
        "lon": 36.82, "lat": -1.29,
    },
    {
        "number": 30, "region": "ASIA-PACIFIC", "field": "INDUSTRIAL FIRE",
        "place": "Serang", "what": "plant fire: 3 dead, 36 missing",
        "source": "Basarnas", "certainty": "CONFIRMED",
        "lon": 106.15, "lat": -6.12,
    },
    {
        "number": 31, "region": "ASIA-PACIFIC", "field": "CRICKET",
        "place": "Wellington", "what": "India 720/9, record in NZ",
        "source": "ESPN, TOI", "certainty": "CONFIRMED",
        "lon": 174.78, "lat": -41.29,
    },
    {
        "number": 32, "region": "ASIA-PACIFIC", "field": "WEATHER",
        "place": "Fukushima", "what": "snowbound guests leave",
        "source": "Village", "certainty": "CONFIRMED",
        "lon": 140.07, "lat": 37.65,
    },
    {
        "number": 33, "region": "ASIA-PACIFIC", "field": "PROTEST",
        "place": "Bangladesh", "what": "~30 homes torched in unrest",
        "source": "PTI", "certainty": "STATED",
        "lon": 90.41, "lat": 23.81,
    },
    {
        "number": 34, "region": "ASIA-PACIFIC", "field": "POLLUTION",
        "place": "Delhi", "what": "air \u2018poor\u2019 4th day, AQI 239",
        "source": "CPCB", "certainty": "CONFIRMED",
        "lon": 77.21, "lat": 28.61,
    },
    {
        "number": 35, "region": "ASIA-PACIFIC", "field": "DEFENCE",
        "place": "Canberra", "what": "Marles slams CBO on AUKUS",
        "source": "Reuters", "certainty": "STATED",
        "lon": 149.13, "lat": -35.28,
    },
    {
        "number": 36, "region": "ASIA-PACIFIC", "field": "MARKETS",
        "place": "China", "what": "margin floor cut to 80%",
        "source": "3 exchanges", "certainty": "CONFIRMED",
        "lon": 121.47, "lat": 31.23,
    },
    {
        "number": 37, "region": "AMERICAS", "field": "MOTORSPORT",
        "place": "Las Vegas", "what": "Verstappen wins the GP",
        "source": "F1", "certainty": "CONFIRMED",
        "lon": -115.14, "lat": 36.17,
    },
    {
        "number": 38, "region": "AMERICAS", "field": "TECH & SPEECH",
        "place": "Bogot\u00e1", "what": "govt asks X to suspend Petro",
        "source": "MinTIC", "certainty": "CONFIRMED",
        "lon": -74.07, "lat": 4.71,
    },
    {
        "number": 39, "region": "AMERICAS", "field": "WEATHER",
        "place": "Brazil", "what": "storm death toll rises to 5",
        "source": "Civil Def.", "certainty": "CONFIRMED",
        "lon": -47.90, "lat": -15.80,
    },
    {
        "number": 40, "region": "AMERICAS", "field": "EARTHQUAKE",
        "place": "Peru", "what": "M5.1 quake near Cerro de Pasco",
        "source": "IGP", "certainty": "CONFIRMED",
        "lon": -76.26, "lat": -10.68,
    },
    {
        "number": 41, "region": "AMERICAS", "field": "HEALTH POLICY",
        "place": "Washington", "what": "El-Sayed: call it TrumpCare",
        "source": "NBC", "certainty": "STATED",
        "lon": -77.04, "lat": 38.90,
    },
    {
        "number": 42, "region": "WORLD", "field": "CRYPTO",
        "place": "Markets", "what": "Bitcoin back above $60k",
        "source": "FXStreet, Fool", "certainty": "CONFIRMED",
        "lon": None, "lat": None,
    },
]

# Topic of every story, derived from its field (section 5.7).  Single
# source of truth: TOPIC_OF_FIELD above.
for _story in STORIES:
    _story["topic"] = TOPIC_OF_FIELD[_story["field"]]

# Total story count, derived from the list (section 6).
N = len(STORIES)

# ---------------------------------------------------------------- top page
# Section 5.1.
DECK_LINE = (
    "COP31 ends with no deal  \u00b7  Russian strike kills 11 near Kyiv  \u00b7  "
    "Russian warship capsized at Benghazi"
)
BACKGROUND_TEXT = (
    "US\u2013Israel war with Iran since Feb 2026  \u00b7  Russia\u2019s war on "
    "Ukraine since 2022  \u00b7  Gaza truce since Oct 2025  \u00b7  "
    "Netanyahu: caretaker PM  \u00b7  US midterms: 3 Nov"
)

# Section 5.2: timeline (UTC).  Each entry: time, event, detail.
TIMELINE = [
    ("00:00", "Khartoum drones", "until 02:30"),
    ("~01:00", "Benghazi blasts", "03:00 local time"),
    ("04:00", "Las Vegas GP", "start; Verstappen wins"),
    ("05:47", "Merkury burns", "satellite image"),
    ("06:00", "COP31 plenary", "resumes, Antalya"),
    ("10:00", "HK polls close", "turnout 98.79%"),
    ("16:30", "Liverpool v Utd", "kick-off; Liverpool 4\u20130"),
    ("17:00", "ATP final", "start; Alcaraz wins"),
]

# Section 5.3: the day in numbers.  Each entry: figure, label.
NUMBERS = [
    ("186", "drones at Ukraine overnight"),
    ("11", "killed in Dymer collapse"),
    ("~200", "nations, no COP31 deal"),
    ("98.79%", "record turnout, Hong Kong"),
    ("258", "House seats for Democrats"),
    ("720/9", "India\u2019s record score in NZ"),
]

# ---------------------------------------------------------------- row A
# Section 5.9: "How the day changed".  Each entry: bold lead-in, then
# regular text that runs on from it.
HOW_CHANGED = [
    ("Dymer:", " 2 dead in the morning \u2192 11 by night"),
    ("COP31:", " final text tabled \u2192 rejected, no deal"),
    ("Merkury:", " fire seen 05:47 \u2192 capsized; attacker unknown"),
]

# Section 5.10: "Date check".  The first line carries a {N} placeholder
# for the story count; fill it with date_check_lines().  Each entry is a
# (bold lead-in, regular text) pair.
DATE_CHECK = [
    ("", "All {N} stories happened, or were first reported, on Sun 22 Nov (UTC)."),
    ("Left out, Sat 21:", " Peru M6.7 quake and its toll, \u2018El Chapo Isidro\u2019 arrest, Bahrain strike."),
    ("Mon 23:", " 49ers\u2013Vikings (kick-off 01:20)."),
]

# Section 5.11: footer legend definitions, in display order.
CERTAINTY_DEFS = [
    ("CONFIRMED", "official source or 2+ outlets named"),
    ("STATED", "one party\u2019s claim, not checked"),
    ("UNVERIFIED", "unconfirmed, or attacker unknown"),
]


# ---------------------------------------------------------------- computed
def region_totals():
    """Story count per region, in REGIONS order.  Computed from STORIES."""
    totals = {region: 0 for region in REGIONS}
    for story in STORIES:
        totals[story["region"]] += 1
    return totals


def topic_totals():
    """Story count per topic, in TOPICS order.  Computed from STORIES."""
    totals = {topic: 0 for topic in TOPICS}
    for story in STORIES:
        totals[story["topic"]] += 1
    return totals


def coverage_matrix():
    """Count per (topic, region) pair.  Computed from STORIES."""
    matrix = {(topic, region): 0 for topic in TOPICS for region in REGIONS}
    for story in STORIES:
        matrix[(story["topic"], story["region"])] += 1
    return matrix


def top_story_per_region():
    """For each region, the number of its first lead/card story: the
    lowest-numbered story of that region among stories 1-13.  Computed
    from STORIES."""
    best = {}
    for story in STORIES:
        if story["number"] > 13:
            continue
        region = story["region"]
        if region not in best or story["number"] < best[region]:
            best[region] = story["number"]
    return best


def no_pin_numbers():
    """Numbers of stories with no map coordinates (no map dot)."""
    return [story["number"] for story in STORIES
            if story.get("lon") is None or story.get("lat") is None]


def date_check_lines(n=None):
    """The date-check lines with the story count filled in.  Defaults to
    the computed total N."""
    if n is None:
        n = N
    return [(lead, text.replace("{N}", str(n))) for lead, text in DATE_CHECK]
