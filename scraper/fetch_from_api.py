from datetime import datetime, timedelta, date
from io import BytesIO
from itertools import cycle
import json
import os
from pathlib import Path
from proxy import get_lime_proxies
from random import randint
import sys
from time import sleep, tzset
import pandas as pd 
import requests
import requests
import logging
import dropbox
from dotenv import load_dotenv
from db import insert_occupancy

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.environ['DROPBOX_ACCESS_TOKEN']
os.environ['TZ'] = 'America/New_York'
tzset()

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.ERROR)
else: 
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', stream=sys.stdout)
logger = logging.getLogger()

UNNECCESARY_LIST_KEYS = ['contextualPictures', 'kickerContent', '__typename', 'formattedBadges']
UNNECCESARY_OCC_KEYS = ['__typename', 'maxNights', 'minNights', 'price']
LOCATIONS = [{'name': 'Georgia, United States', 'id': 'ChIJV4FfHcU28YgR5xBP7BC8hGY'}, 
             {'name': 'North Carolina, United States', 'id': 'ChIJgRo4_MQfVIgRGa4i6fUwP60'}, 
             {'name': 'Florida, United States', 'id': 'ChIJvypWkWV2wYgR0E7HW9MTLvc'}]
HEADERS = {
'authority': 'www.airbnb.com',
'pragma': 'no-cache',
'cache-control': 'no-cache',
'x-csrf-token': 'V4$.airbnb.com$rEXw23thle4$vk9vkplmuoNzGQfDC_xvnAGtOVVZO9FBgEjkLzfuUX8=',
'x-airbnb-api-key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
'x-niobe-short-circuited': 'true',
'dpr': '2',
'device-memory': '8',
'x-airbnb-graphql-platform-client': 'minimalist-niobe',
'content-type': 'application/json',
'x-airbnb-supports-airlock-v2': 'true',
'ect': '4g',
'x-airbnb-graphql-platform': 'web',
'accept': '*/*',
'sec-fetch-site': 'same-origin',
'sec-fetch-mode': 'cors',
'sec-fetch-dest': 'empty',
'accept-language': 'en-US,en;q=0.9,fr;q=0.8',
}
PROXIES = cycle(get_lime_proxies())
TINY_HOUSE_FILE = str(Path.joinpath(Path(__file__).parent, 'output_files', 'tinyHouses.xlsx').absolute())
OCC_FILE = str(Path.joinpath(Path(__file__).parent, 'output_files', f'{date.today():%m-%d-%Y}-occ-data.xlsx').absolute())
OCC_FILE_DROPBOX = f'/Python Projects/Tiny House Scrape Data/{date.today():%m-%d-%Y}-occ-data.xlsx'
def find_occupancy(d):
    if isinstance(d, dict):
        if "__typename" in d and d["__typename"] == "MerlinCalendarDay":
            yield d
        else:
            for v in d.values():
                yield from find_occupancy(v)
    elif isinstance(d, list):
        for v in d:
            yield from find_occupancy(v)
def find_listing(d):
    if isinstance(d, dict):
        if "__typename" in d and d["__typename"] == "ExploreListingItem":
            d['listing']['price'] = d['pricingQuote']['rate']['amount']
            yield d["listing"]
        else:
            for v in d.values():
                yield from find_listing(v)
    elif isinstance(d, list):
        for v in d:
            yield from find_listing(v)
def fetch_listings():          
    itemOffsets = ['0', '20','40', '60', '80']
    listings_each_location = []
    for location in LOCATIONS:
        logger.info(f'Fetching listings for {location}')  
        session = requests.Session()
        session.proxies.update(next(PROXIES))
        listings = []
        for item in itemOffsets:
            url = f"http://www.airbnb.com/api/v3/ExploreSections?operationName=ExploreSections&locale=en&currency=USD&_cb=0ludo940w65gdc06ix23q1d1xqve&variables={{\"isInitialLoad\":true,\"hasLoggedIn\":false,\"cdnCacheSafe\":false,\"source\":\"EXPLORE\",\"exploreRequest\":{{\"metadataOnly\":false,\"version\":\"1.8.3\",\"itemsPerGrid\":20,\"propertyTypeId\":[67],\"placeId\":\"{location['id']}\",\"refinementPaths\":[\"/homes\"],\"tabId\":\"home_tab\",\"flexibleTripLengths\":[\"weekend_trip\"],\"datePickerType\":\"calendar\",\"searchType\":\"unknown\",\"federatedSearchSessionId\":\"2312afab-299b-46f2-b7aa-4a16c58269a5\",\"itemsOffset\":{item},\"sectionOffset\":5,\"query\":\"{location['name']}\",\"cdnCacheSafe\":false,\"treatmentFlags\":[\"flex_destinations_june_2021_launch_web_treatment\",\"new_filter_bar_v2_and_fm_treatment\",\"merch_header_breakpoint_expansion_web\",\"flexible_dates_12_month_lead_time\",\"flex_destinations_nov_2021_category_rank_treatment\",\"storefronts_nov23_2021_homepage_web_treatment\",\"flexible_dates_options_extend_one_three_seven_days\",\"super_date_flexibility\",\"micro_flex_improvements\",\"micro_flex_show_by_default\",\"search_input_placeholder_phrases\",\"pets_fee_treatment\"],\"screenSize\":\"small\",\"isInitialLoad\":true,\"hasLoggedIn\":false}}}}&extensions={{\"persistedQuery\":{{\"version\":1,\"sha256Hash\":\"7e6b7107b26522461b789c09daf5988d6fb7ef224420b8023be21e921f99d6f7\"}}}}"
            response = session.get(url, headers=HEADERS)
            data = json.loads(response.text)
            # TODO api duplicates tiny houses in its response for some reason - only fetching first 20.. needs a fix
            gen = find_listing(data)
            for i in range(20):
                listing = next(gen)
                [listing.pop(key) for key in UNNECCESARY_LIST_KEYS]
                listings.append(listing)
        listings_df = pd.DataFrame.from_dict(listings, orient='columns')
        listings_df.set_index('id', inplace=True)
        listings_df['location_id'] = location['id']
        listings_each_location.append(listings_df)

    with pd.ExcelWriter(TINY_HOUSE_FILE) as writer:
        for i, listing_df in enumerate(listings_each_location):
            listing_df.to_excel(writer, index=True, sheet_name=LOCATIONS[i]['name'])

def fetch_occupancy(id):
    sleep(randint(2, 15))
    logger.info(f'Fetching occupancy for property {id}')
    url = f"https://www.airbnb.com/api/v3/PdpAvailabilityCalendar?operationName=PdpAvailabilityCalendar&locale=en&currency=USD&_cb=0k1durf0yuu6g40ksqy0u1ha5jfo&variables={{\"request\":{{\"count\":6,\"listingId\":\"{id}\",\"month\":{datetime.today().month},\"year\":{datetime.today().year}}}}}&extensions={{\"persistedQuery\":{{\"version\":1,\"sha256Hash\":\"8f08e03c7bd16fcad3c92a3592c19a8b559a0d0855a84028d1163d4733ed9ade\"}}}}"
    bitmap = ''
    try:
        data = requests.get(url, proxies=next(PROXIES), headers=HEADERS).json()
        gen = find_occupancy(data)
        for occ in gen:
            [occ.pop(key) for key in UNNECCESARY_OCC_KEYS]
            # Start accumulating occupancy data including today
            if datetime.strptime(occ['calendarDate'], "%Y-%m-%d") <= datetime.now() - timedelta(days=1):
                continue
            # 0s correspond to availability
            # if you want bitmap to be reflected by UI, will need to change from available to isBooked
            if occ['available']:
                bitmap = bitmap + '0'
            # 1s correspond to bookings
            if not occ['available']: 
                bitmap = bitmap + '1'
    except Exception as e: 
        logger.error(e)
    return [id, bitmap]

def fetch():
    logger.info(f'Beginning scraping for {date.today():%m-%d-%Y}...')
    if not Path(TINY_HOUSE_FILE).is_file():
        fetch_listings()
    listing_dfs = pd.read_excel(TINY_HOUSE_FILE, sheet_name=None)
    occ_dfs = []
    for loc, df in listing_dfs.items():
        occ = df.apply(lambda row: fetch_occupancy(row['id']), axis=1, result_type='expand')
        occ.columns = ['id', 'bitmap']
        occ.set_index('id', inplace=True)
        occ_dfs.append(occ)
    occ_dfs = pd.concat(occ_dfs)
    io = BytesIO()
    with pd.ExcelWriter(io, engine='xlsxwriter') as writer:
        occ_dfs.to_excel(writer, index=True)
    io.seek(0)
    dbx.files_upload(io.read(), OCC_FILE_DROPBOX)
    io.seek(0)
    insert_occupancy(io, date.today())
    logger.info('Scraping complete!')


if __name__ == "__main__":
    print(fetch_occupancy(25975040))
