import logging
import os
import yaml
import csv
import json

def setup_logger():
    logfile = os.path.join("logs", "application_extraction.log")
    logging.basicConfig(filename=logfile, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def log_and_print(string):
    logging.info(string)
    print(string)

def fetch_main_config():
    config_file = os.path.join('config', 'appd_config_extraction.yml')
    try:
        log_and_print('Opening configuration file ' + config_file)
        with open(config_file) as f:
            data = yaml.safe_load(f)
            log_and_print('Full Config Loaded from yaml file: ' + str(data))

    except Exception as err:
        log_and_print('Failed to parse ' + config_file + ' in the following directory ' + os.getcwd())
        log_and_print(err)

    return data['AppDynamics']

def createDirectory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        log_and_print('Created ' + directory_path + ' directory')
# output/appdetails <- here the csv file
# output/appdetails/appname/bt <- here exported BT details



def prepAppDetailsFolders(app_list):
    dirpath = 'output\\appdetails\\' if os.name == "nt" else 'output/appdetails/'
    for app in app_list:
        createDirectory(dirpath + app['name'])

def saveToCsv(directory, filename, data, data_headers):

    sys_path = '\\' if os.name == "nt" else '/'
    filepath = directory + sys_path + filename + '.csv'
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        list_tocsv = []
        list_tocsv.append(data_headers)
        list_tocsv = list_tocsv + (data)
        # using csv.writer method from CSV package
        write = csv.writer(f)
        write.writerows(list_tocsv)
        log_and_print("File " + filename + " saved successfully under: " + filepath)


def saveToJson(directory, filename, data):

    sys_path = '\\' if os.name == "nt" else '/'
    filepath = directory + sys_path + filename + '.json'
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    print(filepath)
    with open(filepath, 'w', encoding='utf-8') as jsonf:
        jsonString = json.dumps(data, indent=4)
        jsonf.write(jsonString)
        log_and_print("File " + filename + " saved successfully under: " + filepath)

def fetchApplicationsFromCsvConfig(config):
    target_app_list = []
    print("THe type: ", type(config))
    with open(config, encoding='utf-8') as df:
        driverReader = csv.DictReader(df)
        for row in driverReader:
            target_app_list.append(row)

    for app in target_app_list:
        # If there is no new application name, then set this to be the same as the old one
        if app['newname'] == '':
            app['newname'] = app['name']
    return target_app_list

# def fetchBtRulesFromCsvConfig(app_list):
#     target_br_rule_list = []
#
#     for app in app_list:
#         filename = os.path.join('output/exported_app_files', app['name'], app['name'] + '_to_import_rules_list.csv')
#         with open(filename, encoding='utf-8') as df:
#             driverReader = csv.DictReader(df)
#             for row in driverReader:
#                 target_br_rule_list.append(row)
#
#     for bt_rule in target_br_rule_list:
#         # If there is no new application name, then set this to be the same as the old one
#         if bt_rule['newname'] == '':
#             bt_rule['newname'] = app['name']
#
#     return target_br_rule_list

def fetchBtRulesFromCsvConfig(app):
    target_br_rule_list = []

    filename = os.path.join('output/exported_app_files', app['name'], app['name'] + '_to_import_rules_list.csv')
    with open(filename, encoding='utf-8') as df:
        driverReader = csv.DictReader(df)
        for row in driverReader:
            target_br_rule_list.append(row)

    for bt_rule in target_br_rule_list:
        # If there is no new application name, then set this to be the same as the old one
        if bt_rule['newname'] == '':
            bt_rule['newname'] = app['name']

    return target_br_rule_list

def read_bt_rule_from_json(appname, bt_name):
    filename = os.path.join('output', 'exported_app_files', appname, 'bt_rules', bt_name + '.json')
    with open(filename, 'r', encoding='utf-8') as jsonf:
        json_string = json.load(jsonf)
        log_and_print("File " + filename + " loaded successfully under: " + filename)
                # Getting the rule json      getting the Scope ID for the post REST Call
        return {'rule': json_string['rule'], 'scope_id': json_string['scopeSummaries'][0]['id']}


