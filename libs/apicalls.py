import asyncio
import json

import requests
from pkg_resources.extern import names
from libs.utilities import log_and_print

# Getting the APM App list
def getAppList(controller_url, auth_token):

    response = requests.get(
        url= controller_url + "controller/rest/applications?output=JSON",
        headers={"Authorization": "Bearer " + auth_token})
    return response.json()

# Function for getting BT Rules for further use in the Script
async def getBtRules(controller_url, auth_token, id):
    
    response = await asyncio.to_thread(requests.get, url = controller_url + '/controller/restui/transactionConfigProto/getRules/' + str(id) + '?output=JSON',
                                      headers={"Authorization": "Bearer " + auth_token})
    # print("BT Rule Request status code: " + str(response.status_code))
    bt_rules = response.json()
    bt_rules = bt_rules['ruleScopeSummaryMappings']

    return bt_rules

async def getBtList(controller_url, auth_token, app_id_or_name):

    response = await asyncio.to_thread(requests.get,
        url= controller_url + "controller/rest/applications/" + app_id_or_name + "/business-transactions?output=JSON",
        headers={"Authorization": "Bearer " + auth_token})
    return response.json()
# Function to get asynchronously all the App Details to be exported
async def getAppDetails(controller_url, auth_token, name,  id):
    bt_rules_list = await getBtRules(controller_url, auth_token, id)
    app_dict = {'name': name , 'id': id, 'bt-rules': bt_rules_list}
    return app_dict

async def post_bt_rule(controller_url, auth_token, app_id,  rule_dict):
    scope_id = rule_dict['scope_id']
    bt_rule = rule_dict['rule']
    bt_rule['version'] += bt_rule['version']
    url = controller_url + 'controller/restui/transactionConfigProto/updateRule?scopeId=' + scope_id + '&applicationId=' + app_id
    print(url)
    print('The rule json')
    print(bt_rule)
    # add version number change because of not it breeaaakes
    response = await asyncio.to_thread(requests.post,
                            url= url, json=bt_rule,
                            headers={"Authorization": "Bearer " + auth_token, 'Accept': '*/*',
             'Accept-Encoding': 'gzip, deflate, br, zstd',
             'Content-Type': 'application/json;charset=UTF-8',})
    return response

def post_bt_rule_non_async(controller_url, auth_token, app_id,  rule_dict, bt_new_name):
    scope_id = rule_dict['scope_id']
    bt_rule = rule_dict['rule']
    bt_rule['version'] = 0
    bt_rule['summary']['name'] = bt_new_name
    url = controller_url + 'controller/restui/transactionConfigProto/createRule?scopeId=' + scope_id + '&applicationId=' + app_id
    print(url)
    print('The rule json')
    print(bt_rule)

    # first create rule and check if it exists
    response = requests.post(
        url=url, json=bt_rule,
        headers={"Authorization": "Bearer " + auth_token, 'Accept': '*/*',
                 'Accept-Encoding': 'gzip, deflate, br, zstd',
                 'Content-Type': 'application/json;charset=UTF-8', })
    response_type = response.json()
     # Assignign the new ID
    print(response.text)
    if response_type['resultType'] == "SUCCESS":
        bt_rule['summary']['id'] = response_type['successes'][0]['summary']['id']
        return response
    else:
        response_type = response_type['messages'][1] # getting the message that the rule already exists

    if response_type == "Rule already exists":
        # add version number change because of not it breeaaakes
        url = controller_url + 'controller/restui/transactionConfigProto/updateRule?scopeId=' + scope_id + '&applicationId=' + app_id
        response =  requests.post(
                                url= url, json=bt_rule,
                                headers={"Authorization": "Bearer " + auth_token, 'Accept': '*/*',
                 'Accept-Encoding': 'gzip, deflate, br, zstd',
                 'Content-Type': 'application/json;charset=UTF-8',})
        response_type = response.json()
        response_type = response_type['resultType']

        while response_type == 'CONFLICT':
            log_and_print("The BT Rule has a 'CONFLICT' - Increasing the version of the current rule and retrying...")
            bt_rule['version'] += 1
            print(bt_rule['version'])
            response = requests.post(
                url=url, json=bt_rule,
                headers={"Authorization": "Bearer " + auth_token, 'Accept': '*/*',
                         'Accept-Encoding': 'gzip, deflate, br, zstd',
                         'Content-Type': 'application/json;charset=UTF-8', })
            print(response.text)
            response_type = response.json()
            response_type = response_type['resultType']
        return response

    # print("This is the response type: ", response_type)

