import json
import requests
from bs4 import BeautifulSoup
import configparser
import pymysql
import time

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
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.connection.cursor()

    def is_sm_firmware_id_exist(self, value):
        sql = "SELECT count(*) as count FROM `firmwares` WHERE `sm_firmware_id`=%s LIMIT 1"
        self.cursor.execute(sql, value)
        result = self.cursor.fetchone()
        return result['count']  # if result['count'] !=0 : firmware exist

    def add_row(self, row_dict):
        # inspired by : https://mail.python.org/pipermail/tutor/2010-December/080701.html
        columns = ", ".join(row_dict)
        values_template = ", ".join(["%s"] * len(row_dict))

        sql = "INSERT INTO `firmwares` (%s) VALUES (%s)" % (columns, values_template)
        values = tuple(row_dict[key] for key in row_dict)

        self.cursor.execute(sql, values)

    def get_sm_firmware_ids(self):
        sm_firmware_ids = []
        sql = "SELECT `sm_firmware_id` FROM `firmwares`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for r in result:
            sm_firmware_ids.append(r['sm_firmware_id'])
        return sm_firmware_ids

    def __del__(self):
        self.cursor.close()
        self.connection.close()


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
    pre_sm_firmware_detail_urls = []

    soup = BeautifulSoup(requests.get(model_url).text, "html.parser")
    rows = soup.find_all("a", class_="firmware-table-row")
    for row in rows:
        href = row["href"]

        # normal url:
        # http://www.sammobile.com/firmwares/download/58156/N916LKLU2COJ4_N916LLUC2COJ4_LUC
        # some firmwares have no detail url, so we have to make an "if" statement

        if href != 'http://www.sammobile.com/firmwares/download//__Unknown':
            sm_firmware_detail_url = href
            t = sm_firmware_detail_url[44:].split('/')
            sm_firmware_id = t[0]
            sm_firmware_detail_url = {sm_firmware_id: sm_firmware_detail_url}

        pre_sm_firmware_detail_urls.append(sm_firmware_detail_url)

    # check if firmware has been added in database for fewer requests
    pre_sm_firmware_detail_urls_dict = eval(str(pre_sm_firmware_detail_urls).replace('{', '').replace('}', '').replace('[', '{').replace(']', '}'))
    sm_firmware_detail_urls = []

    pre_sm_firmware_ids = []
    for d in pre_sm_firmware_detail_urls:
        for (k, v) in d.items():
            pre_sm_firmware_ids.append(k)

    db = SammobileMysql()
    db_ids = db.get_sm_firmware_ids()

    sm_firmware_ids = list((set(pre_sm_firmware_ids)).difference(set(db_ids)))

    for q in sm_firmware_ids:
        sm_firmware_detail_urls.append(pre_sm_firmware_detail_urls_dict[q])

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

keywords = ['Note 5']
model_names = get_model_names(keywords)
for model_name in model_names:
    model_url = get_model_url(model_name)
    sm_firmware_detail_urls = get_sm_firmware_detail_urls(model_url)
    print(len(sm_firmware_detail_urls))
    for sm_firmware_detail_url in sm_firmware_detail_urls:
        time.sleep(10)
        db = SammobileMysql()
        firmware_detail = get_firmware_detail(sm_firmware_detail_url)
        db.add_row(firmware_detail)
        print(firmware_detail['firmware_pda'] + ' added!')
