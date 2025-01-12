import re
from typing import List
import requests
from bs4 import BeautifulSoup
import base64


def find_successful_proxy_servers(proxy_list_url) -> List[dict]:
    proxy_servers = scrape_proxy_list_servers(proxy_list_url)
    return list(filter(lambda server: test_proxy_server(server), proxy_servers))
        
def scrape_proxy_list_servers(proxy_list_url='https://www.us-proxy.org/') -> List[dict]:
    # https secure proxies
    content = requests.get(proxy_list_url).content
    # parsing html response
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', class_='table table-striped table-bordered')
    # iterating through rows in table skipping the header
    proxy_servers = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if tds[4].get_text().lower() == "elite proxy":
            proxy_servers.append({'ip': tds[0].get_text(), 'port': tds[1].get_text()})
    return proxy_servers

def scrape_free_proxy_servers(url='http://free-proxy.cz/en/proxylist/country/all/all/ping/level1'):
    for i in range(1, 2):
        try:
            new_url = f'{url}/{i}'
            content = requests.get(new_url).content
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find(id='proxy_list')
            trs = table.find_all('tr')
            proxy_servers = []
            for tr in trs[1:]:
                tds = tr.find_all('td')
                if len(tds) == 11:
                    ip = tds[0].find('script').text
                    ip = base64.b64decode(ip[ip.find("(\"")+2:ip.find("\")")]).decode('utf-8')
                    port = tds[1].get_text()
                    proxy_servers.append({'ip': ip, 'port': port})
        except Exception as e:
            print(e)
            break
    return proxy_servers

def get_lime_proxies():
    proxies = []
    with open('./proxies.txt') as txt:
        for line in txt:
            proxies.append({'https': line[:5] + "//" + line[5:-1]})
    return proxies
        
    
def test_proxy_server(proxy_config:dict):
    from airbnb_parser import get_driver
    print(f"Verifying proxy {proxy_config['ip']}:{proxy_config['port']}")
    try: 
        driver = get_driver(proxy_config)
        driver.get('https://www.airbnb.com/s/Raleigh/homes?property_type_id%5B%5D=67&place_id=ChIJ9-BRny9arIkRrfARilK2kGc&refinement_paths%5B%5D=%2Fhomes&query=Raleigh&flexible_trip_lengths%5B%5D=weekend_trip&date_picker_type=calendar&click_referer=t%3ASEE_ALL%7Csid%3A3d92c194-4179-468a-970d-7615f23a225a%7Cst%3ASTAYS_LARGE_AREA_DESTINATION_CAROUSELS&search_mode=regular_search&title_type=NONE&last_search_session_id=3d92c194-4179-468a-970d-7615f23a225a&search_type=section_navigation')
        driver.quit()
    except Exception as e:
        print(e)
        return False
    return True
        

if __name__ == "__main__":
    proxies = get_lime_proxies()
    print(requests.get('https://www.airbnb.com', proxies=proxies[0]).content)
   