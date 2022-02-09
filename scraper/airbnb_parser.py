from datetime import date
from typing import List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from proxy import scrape_free_proxy_servers
import json
import logging
import getpass
import os
import sys
import random
import pandas as pd
from multiprocessing import Pool

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

RULES_SEARCH_PAGE = {
    'url': {'tag': 'a', 'get': 'href'},
    'name': {'tag': 'div', 'class': 'c1fwz84r dir dir-ltr'},
    'rating': {'tag': 'span', 'class': 'r1g2zmv6 dir dir-ltr'},
    'price': {'tag': 'span', 'class': '_tyxjp1'},
    'superhost': {'tag': 'div', 'class': 't1qa5xaj dir dir-ltr'},
}

RULES_DETAIL_PAGE = {
    'location': {'tag': 'span', 'class': '_pbq7fmm'},
    'price_per_night': {'tag': 'span', 'class': '_tyxjp1'},
    'guests': {'tag': 'ol'},
    'beds': {'tag': 'ol', 'order': 1},
    'bath': {'tag': 'ol', 'order': 2},    
}

RULES_AMENITIES_PAGE = {
    'bathroom': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Bathroom', 'order': -1},
    'bedroom_and_laundry': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': "Bedroom and laundry", 'order': -1},
    'entertainment': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Entertainment', 'order': -1},
    'home_safety': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Home safety', 'order': -1},    
    'heating_and_cooling': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Heating and cooling', 'order': -1}, 
    'internet_and_office': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Internet and office', 'order': -1}, 
    'kitchen_and_dining': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Kitchen and dining', 'order': -1}, 
    'outdoor': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Outdoor', 'order': -1}, 
    'services': {'tag': 'div', 'class': '_1b2umrx', 'type': 'amenity', 'name': 'Services', 'order': -1}, 

}

def get_driver(config: dict) -> WebDriver:
    
    options = Options()
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    if 'headless' in config and config['headless']:
        options.add_argument('--headless')
    if getpass.getuser() != 'sauravghosal':
        options.binary_location = '/bin/headless-chromium'
        executable_path = '/bin/chromedriver'
    else:
        executable_path = './chromedriver'
    if 'ip' in config and 'port' in config:
        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.ssl_proxy = f'{config["ip"]}:{config["port"]}'
        capabilities = webdriver.DesiredCapabilities.CHROME
        capabilities['acceptSslCerts'] = True
        prox.add_to_capabilities(capabilities)
        return webdriver.Chrome(options=options, executable_path=executable_path, desired_capabilities=capabilities)
    return webdriver.Chrome(options=options, executable_path=executable_path)

def extract_listings(page_url, proxy_config, timeout=20):
    """Extracts all listings from a given page"""
    logger.info(f'Using proxy {proxy_config["ip"]}:{proxy_config["port"]}')
    listings_max = 0
    listings_out = None
    driver = get_driver(proxy_config)
    try:
        driver.get(page_url)
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@itemprop, 'itemListElement')]")))
        soup = BeautifulSoup(driver.page_source, features='html.parser')
        listings = soup.find_all('div', {'itemprop': 'itemListElement'})
        if len(listings) == 20:
            listings_out = listings
        if len(listings) >= listings_max:
            listings_max = len(listings)
            listings_out = listings
    except Exception as e:
        logger.error(e)
        raise TimeoutError
    finally:
        driver.quit()
        if not listings_out:
            raise TimeoutError
    return listings_out
        
        
def extract_element_data(soup: BeautifulSoup, params):
    """Extracts data from a specified HTML element"""
    # 1. Find the right tag
    if 'class' in params: 
        if 'type' in params and params['type'] == 'amenity':
            amenity_names = soup.find_all('div', class_= '_zzc8sqf')
            amenity_index = [amenity.get_text() for amenity in amenity_names].index(params['name'])
            amenity = soup.find_all('div', class_= '_1b2umrx')[amenity_index]
            elements_found = amenity.find_all('div', class_='_gw4xx4')
        else: 
            elements_found = soup.find_all(params['tag'], class_=params['class'])
    else:
         # Handling special case for home info (beds and baths) which are nested in a list
        if params['tag'] == 'ol':
            elements_found = soup.find(params['tag']).find_all('li')
        else: 
            elements_found = soup.find_all(params['tag']) 
    # 2. Extract text from these tags
    if 'get' in params:
        element_texts = [el.get(params['get']) for el in elements_found]
    else:
        element_texts = [el.get_text() for el in elements_found]
    # 3. Select a particular text or concatenate all of them
    tag_order = params.get('order', 0)
    if tag_order == -1:
        output = element_texts
    else:
        output = element_texts[tag_order]
    return output


def extract_listing_features(soup, rules):
    """Extracts all features from the listing"""
    features_dict = {}
    for feature in rules:
        try:
            features_dict[feature] = extract_element_data(soup, rules[feature])
        except Exception as e:
            features_dict[feature] = 'empty'
    
    return features_dict


# updates the occupancies dict with the bitmaps for the next 2 months 
# with 1s corresponding to booked days and 0s corresponding to available days
def scrape_months(page: bytes, occupancies: dict):
    soup = BeautifulSoup(page, features='html.parser')
    # locate calendar
    calendar = soup.find('div', class_='_ge6wj2')
    # parse each month name
    months = calendar.find_all('h3', class_='_14i3z6h')[1:]
    months = [month.get_text() for month in months]
    # scrape occupancy per month
    calendars = calendar.find_all('table')[1:]
    for index, occupancy in enumerate(calendars):   
        dates = occupancy.find_all('td', class_=True)
        bitmap = ''
        for date in dates:
            if date['aria-disabled'] == 'true':
                bitmap += '1'
            else: 
                bitmap += '0'
        occupancies[months[index]] = bitmap
        

# TODO: if connection refused, skip that proxy
def extract_soup_js_and_occupancy_data(url: str, proxies: List, index: int, timeout = [20, 20]):
    # iterating through until finds proxy in list that works
    detail_page = None
    iterations = 1
    while not detail_page and iterations < len(proxies):
        proxy_config = proxies[(index + iterations) % len(proxies)]
        proxy_config['headless'] = True
        logger.info(f"Processing detail page {index} with proxy {proxy_config['ip']}:{proxy_config['port']} on processs {os.getpid()}")
        driver = get_driver(proxy_config)
        try:
            driver.get(url)
            calendar_next = WebDriverWait(driver, timeout[0]).until(EC.element_to_be_clickable((By.XPATH, "(//div[@class='_1w1t1f4']//span[@class='_e296pg'])[2]")))
            occupancies = dict()
            for _ in range(0, 10):
                WebDriverWait(driver, timeout[0]).until(EC.presence_of_element_located((By.XPATH, "//div[@class='_1w1t1f4']//div[@class='_fdp53bg']")))
                scrape_months(driver.page_source, occupancies)
                calendar_next.click()
            detail_page = driver.page_source
        except Exception as e:
            logger.error(e)
            driver.quit()
            iterations += 1
    if not detail_page:
        raise TimeoutError("All proxies timed out for detail page request")
    try: 
        # Launches amenities modal
        # TODO needs debugging for when the button a tag element is not clickable... don't know why this occurs
        amenities_btn = WebDriverWait(driver, timeout[1]).until(EC.element_to_be_clickable((By.XPATH, "//div[@data-section-id='AMENITIES_DEFAULT']//a")))
        amenities_btn.click()
        amenities_modal = WebDriverWait(driver, timeout[1]).until(EC.presence_of_element_located(((By.XPATH, "//div[@class='_17itzz4']//section")))).get_attribute('outerHTML')
        return dict(detail=BeautifulSoup(detail_page, features='html.parser'), amenities=BeautifulSoup(amenities_modal, features='html.parser'), occupancy=dict(occupancies=occupancies))
    except Exception as e:
        logger.error(e)
    finally:
        driver.quit()
    return dict(detail=BeautifulSoup(detail_page, features='html.parser'), occupancy=occupancies)

def scrape_detail_page(base_features, proxies, index):
    """Scrapes the detail page and merges the result with basic features"""
    detailed_url = 'https://www.airbnb.com' + base_features['url']
    detail_page_info = extract_soup_js_and_occupancy_data(detailed_url, proxies, index)

    features_detailed = extract_listing_features(detail_page_info.get('detail'), RULES_DETAIL_PAGE)
    
    features_amenities = extract_listing_features(detail_page_info.get('amenities'), RULES_AMENITIES_PAGE)
    
    occupancies = detail_page_info.get('occupancy')

    features_all = {**base_features, **features_detailed, **features_amenities, **occupancies}
    return features_all


class Parser:
    def __init__(self, link, out_file):
        self.link = link
        self.out_file = out_file
        self.proxies = scrape_free_proxy_servers()

    
    def build_urls(self, listings_per_page=20, pages_per_location=3):
        """Builds links for all search pages for a given location"""
        logger.info(f"Initiating parsing job for {self.link}")
        url_list = []
        for i in range(pages_per_location):
            offset = listings_per_page * i
            url_pagination = self.link + f'&items_offset={offset}'
            url_list.append(url_pagination)
            self.url_list = url_list
        print(self.url_list)


    def process_search_pages(self):
        """Extract features from all search pages"""
        features_list = []
        for index, page in enumerate(self.url_list):
            logger.info(f'Extracting listings from page {index + 1}')
            listings = None
            i = index
            random.shuffle(self.proxies)
            while not listings and i < len(self.proxies):
                proxy_config = self.proxies[i % len(self.proxies)]
                proxy_config['headless'] = False
                try: 
                    listings = extract_listings(page, proxy_config)
                except TimeoutError:
                    i += 1
            for idx, listing in enumerate(listings):   
                features = extract_listing_features(listing, RULES_SEARCH_PAGE)
                features['sp_url'] = self.link
                features_list.append(features)
                logger.info(f"Extracted features from listing {features['url']}")
        self.base_features_list = features_list
        

    def process_detail_pages(self):
        """Runs detail pages processing in parallel"""
        n_pools = os.cpu_count() // 2
        # TODO cycle through proxies if one child process encounters an error
        random.shuffle(self.proxies)
        with Pool(n_pools) as pool:
            params = [(feature, self.proxies, index) for index, feature in enumerate(self.base_features_list)]
            # TODO add in error handling if unable to scrape detail page
            result = pool.starmap_async(scrape_detail_page, params).get()
        self.all_features_list = result


    def save(self, feature_set='all'):
        if feature_set == 'basic':
            pd.DataFrame(self.base_features_list).to_excel(self.out_file, index=False)
        elif feature_set == 'all':
            all_features_list_df = pd.DataFrame(self.all_features_list)
            with pd.ExcelWriter(self.out_file) as writer:
                all_features_list_df.to_excel(writer, index=False)
        logger.info(f"Parsing complete: writing to file")

            
        
    def parse(self):
        self.build_urls()
        self.process_search_pages()
        self.process_detail_pages()
        self.save('all')


if __name__ == "__main__":
    with open('./tinyHouses.json') as f:
        tiny_houses = json.load(f)
    for location, link in tiny_houses.items():
        parser = Parser(link, f'./output_files/{location}_{date.today():%Y-%m-%d}.xlsx')
        parser.parse()