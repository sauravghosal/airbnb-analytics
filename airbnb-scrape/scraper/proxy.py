from typing import List
import requests
from bs4 import BeautifulSoup

def find_successful_proxy_servers(proxy_list_url) -> List[dict]:
    proxy_servers = find_proxy_servers(proxy_list_url)
    return list(filter(lambda server: test_proxy_server(server), proxy_servers))
        
def find_proxy_servers(proxy_list_url) -> List[dict]:
    # https secure proxies
    content = requests.get(proxy_list_url).content
    # parsing html response
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', class_='table table-striped table-bordered')
    # iterating through rows in table skipping the header
    proxy_servers = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        if tds[-2].get_text().lower() == 'yes' and tds[4].get_text().lower() == "elite proxy":
            proxy_servers.append({'ip': tds[0].get_text(), 'port': tds[1].get_text()})
    return proxy_servers[:15]
    
    
def test_proxy_server(proxy_config:dict):
    from airbnb_parser import get_driver
    print(f"Verifying proxy {proxy_config['ip']}:{proxy_config['port']}")
    try: 
        driver = get_driver(proxy_config)
        driver.get('https://www.airbnb.com')
        driver.quit()
    except Exception as e:
        print(e)
        return False
    return True
        

if __name__ == "__main__":
    proxy_servers = find_successful_proxy_servers('https://www.us-proxy.org/')
    print(proxy_servers)
   

    
    