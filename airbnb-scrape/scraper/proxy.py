from typing import List
import requests
from bs4 import BeautifulSoup
   
   
# TODO implement testing of the proxies to ensure they work with airbnb 
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
    return proxy_servers
    
    
def test_proxy_servers():
    pass

if __name__ == "__main__":
    proxy_servers = find_proxy_servers('https://www.us-proxy.org/')
    print(proxy_servers)

    
    