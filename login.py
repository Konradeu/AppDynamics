from libs.utilities import fetch_main_config
from libs.utilities import setup_logger
from libs.utilities import log_and_print

import urllib.parse
import os
import base64
import requests


setup_logger()

def getOauthToken(username, password, controller_url, account):
    auth_credentials = {"grant_type": "client_credentials", "client_id": username + "@" + account,
                        "client_secret": password}
    print(auth_credentials)
    print(controller_url + "/controller/api/oauth/access_token")
    auth_response = requests.post(controller_url + "/controller/api/oauth/access_token", data=auth_credentials,
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    print(auth_response)
    oauth_token = auth_response.json()["access_token"]

    return oauth_token



