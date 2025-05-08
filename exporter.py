import login
import urllib
import os
import base64
import asyncio
import libs.utilities as utils
import libs.apicalls as apicalls
import requests

from libs.utilities import log_and_print

async def main():
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
    app_csvfile = os.path.join('CONFIG', driver_file['ApplicationFile'])

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

    # Getting the APM App list
    app_list = apicalls.getAppList(controllerURL, auth_token)
    # sample app id = 8629


        # bt_list = getBtList(controllerURL, auth_token, '8629')
    # Getting all the details for all the apps in the Controller
    tasks = []
    for app in app_list:
        task = asyncio.create_task(apicalls.getAppDetails(controllerURL, auth_token, app['name'] , str(app['id'])))
        tasks.append(task)
    apps_details = await asyncio.gather(*tasks) # dict

    '''------------------------------------------------------------------------------------------------------------'''

    # Primary processing loop
    app_csv_headers = ['name', 'id', 'newname']
    app_csv_list = []
    bt_rule_csv_header = ['name', 'id', 'enabled', 'newname']


    for app in apps_details:
        app_csv_list.append([app['name'], app['id'], app['name']])
        bt_rule_csv_list = []
        for bt_rule in app['bt-rules']:
            bt_rule_csv_list.append([bt_rule['rule']['summary']['name'], bt_rule['rule']['summary']['id'], bt_rule['rule']['enabled'], bt_rule['rule']['summary']['name']])
            utils.saveToJson('output/exported_app_files/' + app['name'] + '/bt_rules/', bt_rule['rule']['summary']['name'], bt_rule)
        utils.saveToCsv('output/exported_app_files/' + app['name'], app['name'] + '_exported_rules_list', bt_rule_csv_list, bt_rule_csv_header)
        utils.saveToCsv('output/exported_app_files/' + app['name'], app['name'] + '_to_import_rules_list', bt_rule_csv_list, bt_rule_csv_header)

    utils.saveToCsv('output/exported_app_files', 'applist', app_csv_list, app_csv_headers)


    print(apps_details[1])




if __name__ == "__main__":
    asyncio.run(main())