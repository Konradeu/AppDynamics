import login
import urllib
import os
import base64
import asyncio
import libs.utilities as utils
import libs.apicalls as apicalls
from libs.utilities import log_and_print


async def main():
    utils.setup_logger()

    exported_apps_folder = 'output/exported_app_files/'

    main_config = utils.fetch_main_config()
    appd_source_config = main_config['SourceController']
    appd_dest_config = main_config['DestinationController']
    driver_file = main_config['DriverFile']
    controllerURL = appd_source_config['AppdControllerURL']
    userNameAndAccount = urllib.parse.quote(appd_source_config['UserNameAndAccount'])
    encodePassFlag = appd_dest_config['EncodePassFlag']
    userName = urllib.parse.quote(appd_source_config['UserName'])
    password = urllib.parse.quote(appd_source_config['Password'])
    account = appd_source_config['AccountName']
    verify = appd_source_config['Verify']
    proxyFlag = appd_source_config['ProxyFlag']
    proxy = appd_source_config['Proxy']
    appCsvfile = os.path.join('config', driver_file['ApplicationFile'])
    print("THe FIle: ", appCsvfile)
    print(type(appCsvfile))
    if proxyFlag == "True":
        proxies = {'http': proxy,
                   'https': proxy,
                   }
        log_and_print("PROXY CONFIGURED FOR ACCESSING DESTINATION CONTROLLER AS " + str(proxies))
    elif proxyFlag == "False":
        log_and_print(
            "PROXY FLAG SET TO FALSE - SO NO PROXY CONFIGURED IN REQUESTS FOR ACCESSING DESTINATION CONTROLLER")
    else:
        log_and_print("PROXY FLAG NOT SET FOR DESTINATION CONTROLLER - IT MUST BE SET TO EITHER 'True' OR 'False'")
        exit(2)

    if encodePassFlag == "True":
        password = base64.b64decode(password.decode("utf-8"))

    userPassword = base64.b64encode(password.encode())
    print(userNameAndAccount)
    print(type(userPassword))
    print(userName)

    if not controllerURL.endswith('/'):
        controllerURL += '/'


    auth_token = login.getOauthToken(userName, password, controllerURL, account)

    print(controllerURL)
    
    importing_app_list = utils.fetchApplicationsFromCsvConfig('config/application_list.csv')
    # importing_bt_rules = utils.fetchBtRulesFromCsvConfig(importing_app_list)

    for app in importing_app_list:
        tasks = []
        importing_bt_rules = utils.fetchBtRulesFromCsvConfig(app)
        for bt_rule in importing_bt_rules:
            bt_json_dict = utils.read_bt_rule_from_json(app['name'], bt_rule['name'])
            bt_new_name = bt_rule['newname']
            # tasks.append(asyncio.create_task(apicalls.post_bt_rule(controllerURL, auth_token, app['id'], bt_json_dict)))
            response = apicalls.post_bt_rule_non_async(controllerURL, auth_token, app['id'], bt_json_dict, bt_new_name)
        # responses = await asyncio.gather(*tasks)
        # print(type(responses))
        # print(responses)

if __name__ == "__main__":
    asyncio.run(main())
