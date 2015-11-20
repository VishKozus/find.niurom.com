# steps:
# 1. keywords -> model_url
# 2. model_url -> firmware_url
# 3. firmware_url -> firmware_detail
# 4. firmware_detail -> database

import json
import requests
from bs4 import BeautifulSoup
import configparser
import pymysql


def get_model_names(keywords):
    model_names = []

    for keyword in keywords:

        url = "http://www.sammobile.com/wp-content/themes/sammobile-4/templates/fw-page/ajax/ajax.search.php"
        payload = {'term': keyword}
        keyword_models = json.loads(requests.get(url, params=payload).text)

        # models_sample =
        #   [
        #       {
        #           'value': 'GALAXY Note 4 LTE Duos (SM-N9100)',
        #           'url': '/firmwares/database/SM-N9100',
        #           'id': 'SM-N9100'
        #       },
        #       {
        #           ......
        #       }
        #   ]

        keyword_model_names = []

        for keyword_model in keyword_models:
            keyword_model_name = keyword_model['id']
            keyword_model_names.append(keyword_model_name)

        model_names.extend(keyword_model_names)

    return model_names


def get_model_url(model_name):
    base = 'http://www.sammobile.com/firmwares/database/'
    model_url = base + model_name
    return model_url


def get_sm_firmware_detail_urls(model_url):
    sm_firmware_detail_urls = []

    soup = BeautifulSoup(requests.get(model_url).text, "html.parser")
    rows = soup.find_all("a", class_="firmware-table-row")
    for row in rows:
        href = row["href"]

        # normal url:
        # http://www.sammobile.com/firmwares/download/58156/N916LKLU2COJ4_N916LLUC2COJ4_LUC
        # some firmwares have no detail url, so we have to make an "if" statement

        if href != 'http://www.sammobile.com/firmwares/download//__Unknown':
            sm_firmware_detail_url = href

        sm_firmware_detail_urls.append(sm_firmware_detail_url)

    return sm_firmware_detail_urls


def get_firmware_detail(sm_firmware_detail_url):
    data = requests.get(sm_firmware_detail_url)
    soup = BeautifulSoup(data.text, "html.parser")

    firmware_detail = {}

    # |<--------------- 44 characters----------->|
    # http://www.sammobile.com/firmwares/download/58156/N916LKLU2COJ4_N916LLUC2COJ4_LUC
    t = sm_firmware_detail_url[44:].split('/')
    sm_firmware_id = t[0]
    firmware_detail.setdefault('sm_firmware_id', sm_firmware_id)

    firmware_detail.setdefault('sm_firmware_detail_url', sm_firmware_detail_url)
    firmware_detail.setdefault('sm_firmware_download_url', sm_firmware_detail_url.replace('download', 'confirm'))
    firmware_detail.setdefault('baidu_download_url', "")
    firmware_detail.setdefault('baidu_download_secret', "")

    soup_properties = {
        "model_name": "Model",
        "model_series": "Model name",
        "firmware_country_carrier": "Country",
        "firmware_android_version": "Version",
        "firmware_changelist": "Changelist",
        "firmware_build_date": "Build date",
        "firmware_area_code": "Product code",
        "firmware_pda": "PDA",
        "firmware_csc": "CSC"
    }

    for soup_property in soup_properties:
        firmware_detail.setdefault(soup_property, soup.find('td', text=soup_properties[soup_property]).find_next(
            "td").get_text().strip())

    sm_model_url = 'http://www.sammobile.com/firmwares/database/' + firmware_detail['model_name'] + '/'
    firmware_detail.setdefault('sm_model_url', sm_model_url)

    return firmware_detail


# keywords = ['Note 3', 'Note 4', 'Note 5', 'Note Edge']

# keywords = ['Note 5']
# model_names = get_model_names(keywords)
# for model_name in model_names:
#     model_url = get_model_url(model_name)
#     sm_firmware_detail_urls = get_sm_firmware_detail_urls(model_url)
#     for sm_firmware_detail_url in sm_firmware_detail_urls:
#         firmware_detail = get_firmware_detail(sm_firmware_detail_url)
#         print(firmware_detail)


class SammobileMysql:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.host = config['mysql']['host']
        self.user = config['mysql']['user']
        self.password = config['mysql']['password']
        self.db = config['mysql']['db']
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            charset='utf8')
        self.cursor = self.connection.cursor()

    def is_exist(self, key, value):
        sql = "SELECT (1) FROM `firmwares` WHERE %s=%s LIMIT 1"
        if self.cursor.execute(sql, (key, value)):
            return 1

    def insert_sample(self, sample):
        placeholders = ', '.join(['%s'] * len(sample))
        columns = ', '.join(sample.keys())
        sql = "INSERT INTO `firmwares` ( %s ) VALUES ( %s )" % (columns, placeholders)
        print(sql)
        self.cursor.execute(sql, sample.values())
        self.connection.commit()

    def __del__(self):
        self.cursor.close()
        self.connection.close()

db = SammobileMysql()
# print(db.is_exist('sm_firmware_id', '5471438'))


sample = {'firmware_country_carrier': 'China (Open China)', 'baidu_download_secret': '', 'sm_model_url': 'http://www.sammobile.com/firmwares/database/SM-N9200/', 'firmware_changelist': '5970428', 'baidu_download_url': '', 'sm_firmware_id': '59300', 'sm_firmware_download_url': 'http://www.sammobile.com/firmwares/confirm/59300/N9200ZCU2AOJ9_N9200CHC2AOJ9_CHC', 'firmware_android_version': 'Android 5.1.1', 'sm_firmware_detail_url': 'http://www.sammobile.com/firmwares/download/59300/N9200ZCU2AOJ9_N9200CHC2AOJ9_CHC', 'firmware_pda': 'N9200ZCU2AOJ9', 'model_series': 'GALAXY Note 5', 'firmware_csc': 'N9200CHC2AOJ9', 'firmware_area_code': 'CHC', 'firmware_build_date': 'Thu, 22 Oct 2015 12:11:33 +0000', 'model_name': 'SM-N9200'}

db.insert_sample(sample)
