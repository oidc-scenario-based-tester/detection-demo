import sys
import os
import json
import time
from bs4 import BeautifulSoup

from osbtlib import BrowserSimulator, Osbtlib

# set endpoints
HONEST_RP_ENDPOINT = "http://localhost:3000"
HONEST_OP_ENDPOINT = "http://localhost:3001"
PROXY_SERVER_ENDPOINT = "http://localhost:8080"
PROXY_EXTENSION_ENDPOINT = "http://localhost:5555"

# victim credentials
victim_username = 'guest'
victim_password = 'guest'

# create instance of osbtlib
osbt = Osbtlib(
    proxy_extension_url = PROXY_EXTENSION_ENDPOINT
)

try:
    # define browser operations (attacker)
    bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    # run browser operations
    bs.run(sso_flow)

    # get callback url from requestbin history
    traces = osbt.proxy.get_history()
    content = traces['request'][len(traces['request'])-1]['content']
    id_token = json.loads(content)['id_token']

    bs.visit(f'{HONEST_RP_ENDPOINT}/callback#id_token={id_token}')
    time.sleep(1)
    html_content = bs.get_content()
    soup = BeautifulSoup(html_content, 'html.parser')
    response_elem = soup.find(id="response")
    print(response_elem.text)
    assert "Login successful" in response_elem.text
    osbt.proxy.clean()
    bs.close()

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()