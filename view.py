import configparser
import pymysql
import path


class ViewMysql:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(path.home_path + '/config.ini')

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

    def new_firmwares(self):
        sql = "SELECT * FROM `firmwares` ORDER BY `sm_firmware_id` DESC LIMIT 50"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        return result

# db = ViewMysql()
# print(db.new_firmwares())
