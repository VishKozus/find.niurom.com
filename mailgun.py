import configparser
import requests


def send_mail(content):

    config = configparser.ConfigParser()
    config.read('config.ini')

    interface = config['email']['interface']
    auth = (config['email']['auth_type'], config['email']['auth_key'])
    mail = {
        "from": "新固件通知 <mailgun@sandbox88ebd7dc8fac41cc8afe7b7b6f4fcb54.mailgun.org>",
        "to": config['email']['mail_to'],
        "subject": "有新固件增加",
        "text": content
    }
    result = requests.post(interface, auth=auth, data=mail)

    return result
