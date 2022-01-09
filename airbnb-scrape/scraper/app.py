import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from proxy import find_proxy_servers
import logging
import requests


logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    proxy_servers = find_proxy_servers('https://sslproxies.org/')
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.binary_location = '/bin/headless-chromium'    
    driver = webdriver.Chrome(options=options, executable_path='/bin/chromedriver', service_log_path='/tmp/chromedriver.log')
    driver.get('https://sslproxies.org/')
    driver.implicitly_wait(10)
    print(driver.page_source)
    driver.quit()



    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "hello world",
                # "location": ip.text.replace("\n", "")
            }
        ),
    }
