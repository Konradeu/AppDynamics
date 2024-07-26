import threading
import requests
import asyncio

hasLoad = {}
loadLock = threading.Lock()

'''Functions'''
# Function for getting AppID for further use in the Script

def restGetCall(controllerUrl, authentication_token, api):
    requestGetUrL = controllerUrl + '/controller' + api + 'output=JSON'
    DataResponse = requests.get(requestGetUrL, headers={"Authorization": "Bearer " + authentication_token})
    return DataResponse.json()

async def asyncRestGetCall(controllerUrl, authentication_token, api):
    requestGetUrL = controllerUrl + '/controller' + api + 'output=JSON'
    DataResponse = await asyncio.to_thread(requests.get, requestGetUrL, headers={"Authorization": "Bearer " + authentication_token})
    return DataResponse.json()

def getAppID(controllerURL, appName, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications?output=JSON'
    appDataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    print("App Request status code: " + str(appDataResponse.status_code))
    appList = appDataResponse.json()
    for app in appList:
        if app['name'] == appName:
            return app['id']
        else:
            continue
    return 'No ID for that App Name has been found'

# Function for getting BT Rules for further use in the Script
def getBtRules(controllerURL, appID, authentication_token):
    requestGetURL = controllerURL + '/controller/restui/transactionConfigProto/getRules/' + str(appID) + '?output=JSON'
    btRuleDataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    print("BT Rule Request status code: " + str(btRuleDataResponse.status_code))
    btRules = btRuleDataResponse.json()

    rulesList = []
    rulesEnabledList = []
    for rule in btRules['ruleScopeSummaryMappings']:
        rulesList.append(rule['rule']['summary']['name'])
        rulesEnabledList.append(rule['rule']['enabled'])
    return rulesList, rulesEnabledList

# Function for getting Response time, to check whether a BT has load or nor for the getBTs function
async def getBtMetric(controllerURL, appName, tierName, btName, timeInMin, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications/' + appName + '/metric-data?output=JSON&metric-path=Business%20Transaction%20Performance%7CBusiness%20Transactions%7C' + tierName + '%7C'+ btName + '%7CAverage%20Response%20Time%20%28ms%29&time-range-type=BEFORE_NOW&duration-in-mins=' + str(timeInMin)
    metricDataResponse = await asyncio.to_thread(requests.get,requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    metrics = metricDataResponse.json()
    if len(metrics) == 0:
        return 'No'
    elif metrics[0]['metricName'] == 'METRIC DATA NOT FOUND':
        return 'No'
    else:
        return 'Yes'

def getBTTarget(controllerURL, appName, tierName, btName, timeInMin, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications/' + appName + '/metric-data?output=JSON&metric-path=Business%20Transaction%20Performance%7CBusiness%20Transactions%7C' + tierName + '%7C' + btName + '%7CAverage%20Response%20Time%20%28ms%29&time-range-type=BEFORE_NOW&duration-in-mins=' + str(
        timeInMin)
    metricDataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    metrics = metricDataResponse.json()
    global loadLock
    loadLock.acquire()
    global hasLoad
    if len(metrics) == 0:
        hasLoad[btName] = 'No'
    elif metrics[0]['metricName'] == 'METRIC DATA NOT FOUND':
        hasLoad[btName] = 'No'
    else:
        hasLoad[btName] = 'Yes'
    loadLock.release()


# Function for getting the BT List from a controller and saving the names, used rules and entry point type to a dict
async def getBTs(controllerURL, appName, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications/' + appName + '/business-transactions?output=JSON'
    btDataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    print("BT Request status code: " + str(btDataResponse.status_code))
    btlist = btDataResponse.json()
    namesList = []
    ruleList = []
    entryTypeList = []
    tierNameList = []
    hasLoad = []
    tasks = [] # this is for the async tasks
    print("Gathering BTs data...")
    for element in btlist:
        namesList.append(element['name'])
        ruleList.append(element['rule'])
        entryTypeList.append(element['entryPointTypeString'])
        tierNameList.append(element['tierName'])
        task = asyncio.create_task(getBtMetric(controllerURL, appName, element['tierName'], element['name'], 720, authentication_token))
        tasks.append(task)

    hasLoad = await asyncio.gather(*tasks)
    await asyncio.sleep(2)
    return {'BT names': namesList, 'Has load?': hasLoad, 'Used Rule': ruleList, 'Entry Point': entryTypeList, "Tier": tierNameList}

def getTiers(controllerURL, appName, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications/' + appName + '/tiers?output=JSON'
    tierDataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    print("Tier Request status code: " + str(tierDataResponse.status_code))
    tierList = tierDataResponse.json()

    tierNameList = []
    tierStatusList = []
    for tier in tierList:
        tierNameList.append(tier['name'])
        if tier['numberOfNodes'] != 0 : tierStatusList.append('Active')
        else: tierStatusList.append('Innactive')

    return tierNameList, tierStatusList

async def applicationCheck(controllerURL, authentication_token):
    requestGetURL = controllerURL + '/controller/rest/applications/?output=JSON'
    DataResponse = requests.get(requestGetURL, headers={"Authorization": "Bearer " + authentication_token})
    print("AppCheck Request status code: " + str(DataResponse.status_code))
    List = DataResponse.json()

    applicationNameList = []
    applicationStatusList = []
    resultList = []
    tasks = []
    for element in List:
        apiCall = '/rest/applications/' + element['name']  + '/metric-data?metric-path=Overall%20Application%20Performance%7CCalls%20per%20Minute&time-range-type=BEFORE_NOW&duration-in-mins=720&'
        task = asyncio.create_task(asyncRestGetCall(controllerURL, authentication_token, apiCall))
        tasks.append(task)
    responses = await asyncio.gather(*tasks)

    # Add here async
    for element, result in zip(List, responses):
        applicationNameList.append(element['name'])
        jsonmetricresponse = result
        if len(jsonmetricresponse) != 0 and jsonmetricresponse[0]['metricValues'] != []: applicationStatusList.append('Active')
        elif len(jsonmetricresponse) and jsonmetricresponse[0]['metricValues'] == [] : applicationStatusList.append('Innactive')
        elif len(jsonmetricresponse) == 0: applicationStatusList.append('Innactive')
    return applicationNameList, applicationStatusList


def fillingList(list1, list2, list3, list4):
    if len(list1) > len(list3):
        for i in range(len(list1) - len(list3)):
            list3.append('-')
            list4.append('-')
    elif len(list1) < len(list3):
        for i in range(len(list3) - len(list1)):
            list1.append('-')
            list2.append('-')
    return list1, list2, list3, list4

def elemntComparison(prodList1, prodList2, stagingList1, stagingList2):
    prodDict = dict(zip(prodList1, prodList2))
    stagingDict = dict(zip(stagingList1, stagingList2))
    dict_intersection = (prodDict.keys() & stagingDict.keys())

    prod_intersection_status = []
    staging_intersection_status = []

    newProdDict = {}
    newStagingDict = {}

    for key in dict_intersection:
        if key in prodDict.keys():
            prod_intersection_status.append(prodDict[key])
            newProdDict[key] = prodDict.pop(key)

        if key in stagingDict.keys():
            staging_intersection_status.append(stagingDict[key])
            newStagingDict[key] = stagingDict.pop(key)

    dict_intersection = dict(zip(dict_intersection, prod_intersection_status))


    newProdDict.update(prodDict)

    newStagingDict.update(stagingDict)

    prodList1 = list(newProdDict.keys())
    prodList2 = list(newProdDict.values())
    stagingList1 = list(newStagingDict.keys())
    stagingList2 = list(newStagingDict.values())

    prodList1, prodList2, stagingList1, stagingList2 = fillingList(prodList1, prodList2, stagingList1, stagingList2)

    if len(prodList1) > len(stagingList1):
        is_in_both_envs = ['No'] * len(prodList1)
    elif len(prodList1) < len(stagingList1):
        is_in_both_envs = ['No'] * len(stagingList1)
    elif len(prodList1) == len(stagingList1):
        is_in_both_envs = ['No'] * len(prodList1)

    for i, rule in enumerate(dict_intersection.keys()):
        if rule in prodList1:
            is_in_both_envs[i] = 'Yes'

    return prodList1, prodList2, stagingList1, stagingList2, is_in_both_envs

def fillingList(list1, list2, list3, list4):
    if len(list1) > len(list3):
        for i in range(len(list1) - len(list3)):
            list3.append('-')
            list4.append('-')
    elif len(list1) < len(list3):
        for i in range(len(list3) - len(list1)):
            list1.append('-')
            list2.append('-')
    return list1, list2, list3, list4

class ApiClient:
    def __init__(self, api_secret, api_username, controller_url, controller_account, app):
        self.api_secret = api_secret
        self.api_username = api_username
        self.controller_url = controller_url
        self.controller_account = controller_account
        self.app = app

    RuleNamesList = []
    RuleEnabledList = []
    DataDict = {}
    TiersNameList = []
    TiersStatusList = []
    authToken = ""
    AppID = ""
    DataFrame = ''

class EumRule():
    def __init__(self, kind, name, type, value, enabled):
        self.kind = kind
        self.name = name
        self.type = type
        self.value = value
        self.enabled = enabled




class EumApp():
    def __init__(self, name, id, appKey, active):
        self.name = name
        self.id = id
        self.appKey = appKey
        self.active = active
        self.basePageRulesList = {}
        self.ajaxRulesList = {}
        self.virtualPagesRuleslist = {}

    def getName(self):
        return self.name

    def getId(self):
        return self.id

    def getAppKey(self):
        return self.appKey

    def getActive(self):
        return self.active

    def getRulesDict(self, apptype):
        includeRules = {apptype + 'Kind': [e.kind for e in self.basePageRulesList['Include']],
         apptype + 'Name': [e.name for e in self.basePageRulesList['Include']],
         apptype + 'Type': [e.type for e in self.basePageRulesList['Include']],
         apptype + 'Value': [e.value for e in self.basePageRulesList['Include']],
         apptype + 'Enabled': [e.enabled for e in self.basePageRulesList['Include']]}

        includeRules[apptype + 'Kind'] += [e.kind for e in self.ajaxRulesList['Include']]
        includeRules[apptype + 'Name'] += [e.name for e in self.ajaxRulesList['Include']]
        includeRules[apptype + 'Type'] += [e.type for e in self.ajaxRulesList['Include']]
        includeRules[apptype + 'Value'] += [e.value for e in self.ajaxRulesList['Include']]
        includeRules[apptype + 'Enabled'] += [e.enabled for e in self.ajaxRulesList['Include']]

        includeRules[apptype + 'Kind'] += [e.kind for e in self.virtualPagesRuleslist['Include']]
        includeRules[apptype + 'Name'] += [e.name for e in self.virtualPagesRuleslist['Include']]
        includeRules[apptype + 'Type'] += [e.type for e in self.virtualPagesRuleslist['Include']]
        includeRules[apptype + 'Value'] += [e.value for e in self.virtualPagesRuleslist['Include']]
        includeRules[apptype + 'Enabled'] += [e.enabled for e in self.virtualPagesRuleslist['Include']]


        excludeRules = {apptype + 'Kind': [e.kind for e in self.basePageRulesList['Exclude']],
                            apptype + 'Name': [e.name for e in self.basePageRulesList['Exclude']],
                            apptype + 'Type': [e.type for e in self.basePageRulesList['Exclude']],
                            apptype + 'Value': [e.value for e in self.basePageRulesList['Exclude']],
                            apptype + 'Enabled': [e.enabled for e in self.basePageRulesList['Exclude']]}

        excludeRules[apptype + 'Kind'] += [e.kind for e in self.ajaxRulesList['Exclude']]
        excludeRules[apptype + 'Name'] += [e.name for e in self.ajaxRulesList['Exclude']]
        excludeRules[apptype + 'Type'] += [e.type for e in self.ajaxRulesList['Exclude']]
        excludeRules[apptype + 'Value'] += [e.value for e in self.ajaxRulesList['Exclude']]
        excludeRules[apptype + 'Enabled'] += [e.enabled for e in self.ajaxRulesList['Exclude']]

        excludeRules[apptype + 'Kind'] += [e.kind for e in self.virtualPagesRuleslist['Exclude']]
        excludeRules[apptype + 'Name'] += [e.name for e in self.virtualPagesRuleslist['Exclude']]
        excludeRules[apptype + 'Type'] += [e.type for e in self.virtualPagesRuleslist['Exclude']]
        excludeRules[apptype + 'Value'] += [e.value for e in self.virtualPagesRuleslist['Exclude']]
        excludeRules[apptype + 'Enabled'] += [e.enabled for e in self.virtualPagesRuleslist['Exclude']]

        return {'Includes': includeRules, 'Excludes': excludeRules}


def getEumApps(controllerURL, authentication_token):
    list = restGetCall(controllerURL, authentication_token, '/restui/eumApplications/getAllEumApplicationsData?time-range=last_1_hour.BEFORE_NOW.-1.-1.60&')
    objs = []

    for i, element in enumerate(list):
        active = 'No'
        if element['metrics']['pageRequestsPerMin']['name'] != "METRIC DATA NOT FOUND": active = 'Yes'


        objs.append(EumApp(name=element['name'], id=element['id'], appKey=element['appKey'], active=active))

    return objs

def eumRuleExtraction(fullRulesList, kind):
    ruleIncludeList = []
    ruleExcludeList = []
    for rule in fullRulesList['customNamingIncludeRules']:
        if rule['isDefault'] == True:
            continue
        else:
            ruleIncludeList.append(EumRule(kind=kind, name=rule['name'], type=rule['matchOnURL']['type'], value=rule['matchOnURL']['value'], enabled=rule['enabled']))
    if len(fullRulesList['customNamingExcludeRules']) != 0:
        for rule in fullRulesList['customNamingExcludeRules']:
            ruleExcludeList.append(EumRule(kind=kind, name=rule['name'], type=rule['matchOnURL']['type'], value=rule['matchOnURL']['value'], enabled=rule['enabled']))
    return ruleIncludeList, ruleExcludeList

def getEumRules(controllerURL, authentication_token, appname, appList, apptype):
    for i, app in enumerate(appList):
        if app.name == appname:
            appId = app.id
            appwithrulesIterator = i
            basePageRulesList = restGetCall(controllerURL, authentication_token,
                                            '/restui/browserRUMConfig/getPagesAndFramesConfig/' + str(appId) + '?')
            ajaxRulesList = restGetCall(controllerURL, authentication_token,
                                        '/restui/browserRUMConfig/getAJAXConfig/' + str(appId) + '?')
            virtualPagesRuleslist = restGetCall(controllerURL, authentication_token,
                                                '/restui/browserRUMConfig/getVirtualPagesConfig/' + str(appId) + '?')

            basePageIncludeRuleObjects, basePageExcludeRuleObjects = eumRuleExtraction(basePageRulesList, 'BasePage')
            ajaxIncludeRuleObjects, ajaxExcludeRuleObjects = eumRuleExtraction(ajaxRulesList, 'Ajax')
            virtualPageIncludeRuleObjects, virtualPageExcludeRuleObjects = eumRuleExtraction(virtualPagesRuleslist, 'VirtualPage')
            app.basePageRulesList['Include'] = basePageIncludeRuleObjects
            app.basePageRulesList['Exclude'] = basePageExcludeRuleObjects
            app.ajaxRulesList['Include'] = ajaxIncludeRuleObjects
            app.ajaxRulesList['Exclude'] = ajaxExcludeRuleObjects
            app.virtualPagesRuleslist['Include'] = virtualPageIncludeRuleObjects
            app.virtualPagesRuleslist['Exclude'] = virtualPageExcludeRuleObjects

            return appwithrulesIterator, app.getRulesDict(apptype)

sort_order = {'b': 1, 'a': 2, 'v': 3}
# Custom sort function that uses the first letter to determine sort order
def sort_key(word):
    first_letter = word[0].lower()  # Convert the first letter to lowercase for case-insensitive sorting
    # Use the sort_order if the first letter matches 'b', 'a', or 'v'; otherwise, use a default order
    return (sort_order.get(first_letter, 4), word)
def fillAndConcatenateDicts(dict1, dict2):
    maxLen = 0

    prodDict = {'kind': dict1['ProdKind'], 'name': dict1['ProdName']}
    stagingDict = {'kind': dict2['StagingKind'], 'name': dict2['StagingName']}
    prodList = [k + n for k, n in zip(dict1['ProdKind'], dict1['ProdName'])]
    stagingList = [k + n for k, n in zip(dict2['StagingKind'], dict2['StagingName'])]
    list_intersection = list(set(prodList).intersection(set(stagingList)))

    list_intersection = sorted(list_intersection, key=sort_key)

    for intersect in list_intersection:
        if intersect in prodList and intersect in stagingList:
            if len(dict1['ProdName']) > len(dict2['StagingName']):
                prdIndex = prodList.index(intersect)
                tmpInter = prodList.pop(prdIndex)
                stagingIndex = stagingList.index(intersect)

                tmpkind = dict1['ProdKind'].pop(prdIndex)
                tmpname = dict1['ProdName'].pop(prdIndex)
                tmptype = dict1['ProdType'].pop(prdIndex)
                tmpvalue = dict1['ProdValue'].pop(prdIndex)
                tmpenabled = dict1['ProdEnabled'].pop(prdIndex)

                prodList.insert(stagingIndex, tmpInter)
                dict1['ProdKind'].insert(stagingIndex, tmpkind)
                dict1['ProdName'].insert(stagingIndex, tmpname)
                dict1['ProdType'].insert(stagingIndex, tmptype)
                dict1['ProdValue'].insert(stagingIndex, tmpvalue)
                dict1['ProdEnabled'].insert(stagingIndex, tmpenabled)


            elif len(dict1['ProdName']) < len(dict2['StagingName']):

                stagingIndex = stagingList.index(intersect)
                tmpInter = stagingList.pop(stagingIndex)
                prdIndex = prodList.index(intersect)

                tmpkind = dict2['StagingKind'].pop(stagingIndex)
                tmpname = dict2['StagingName'].pop(stagingIndex)
                tmptype = dict2['StagingType'].pop(stagingIndex)
                tmpvalue = dict2['StagingValue'].pop(stagingIndex)
                tmpenabled = dict2['StagingEnabled'].pop(stagingIndex)

                stagingList.insert(prdIndex, tmpInter)
                dict2['StagingKind'].insert(prdIndex, tmpkind)
                dict2['StagingName'].insert(prdIndex, tmpname)
                dict2['StagingType'].insert(prdIndex, tmptype)
                dict2['StagingValue'].insert(prdIndex, tmpvalue)
                dict2['StagingEnabled'].insert(prdIndex, tmpenabled)

            else:
                prdIndex = prodList.index(intersect)
                tmpInter = prodList.pop(prdIndex)
                stagingIndex = stagingList.index(intersect)

                tmpkind = dict1['ProdKind'].pop(prdIndex)
                tmpname = dict1['ProdName'].pop(prdIndex)
                tmptype = dict1['ProdType'].pop(prdIndex)
                tmpvalue = dict1['ProdValue'].pop(prdIndex)
                tmpenabled = dict1['ProdEnabled'].pop(prdIndex)

                prodList.insert(stagingIndex, tmpInter)
                dict1['ProdKind'].insert(stagingIndex, tmpkind)
                dict1['ProdName'].insert(stagingIndex, tmpname)
                dict1['ProdType'].insert(stagingIndex, tmptype)
                dict1['ProdValue'].insert(stagingIndex, tmpvalue)
                dict1['ProdEnabled'].insert(stagingIndex, tmpenabled)

    if len(dict1['ProdName']) > len(dict2['StagingName']):
        is_in_both_envs = ['No'] * len(dict1['ProdName'])
    elif len(dict1['ProdName']) < len(dict2['StagingName']):
        is_in_both_envs = ['No'] * len(dict2['StagingName'])
    elif dict1['ProdName'] == len(dict2['StagingName']):
        is_in_both_envs = ['No'] * dict1['ProdName']

    for rule in list_intersection:
        prdIndex = prodList.index(rule)
        if isinstance(prodList.index(rule), int) == True:
            is_in_both_envs[prdIndex] = 'Yes'

    for d in dict1.values():
        if len(d) > maxLen: maxLen = len(d)
        else: continue
    for d in dict2.values():
        if len(d) > maxLen: maxLen = len(d)
        else: continue

    for d in dict1.values():
        if len(d) < maxLen:
            for i in range(maxLen - len(d)):
                d.append('-')
    for d in dict2.values():
        if len(d) < maxLen:
            for i in range(maxLen - len(d)):
                d.append('-')





    return dict1 | dict2 | {'InBothEnvs': is_in_both_envs}




