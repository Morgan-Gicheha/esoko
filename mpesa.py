from datetime import datetime

import requests
import base64
from requests.auth import HTTPBasicAuth
#oauth/v1/generate?grant_type=client_credentials

base_url = 'https://sandbox.safaricom.co.ke/'  

consumer_Key = 'hlDi7YbAE8CUKjK0Bih18hdyxFB7HtH4'
consumer_secret = 'h3ZtmG7JGD4ydRLa'
BusinessShortCode = '174379'
passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'


def getTimeStamp():
    sai = datetime.now()
    sai_string = sai.strftime("%Y%m%d%H%M%S")

    return sai_string


def genPassword():
        '''This is the password used for encrypting the request sent: A base64 encoded string. (The base64 string is a combination of Shortcode+Passkey+Timestamp) '''
        mpesaToEncryptPassword = BusinessShortCode + passkey + getTimeStamp()
        mpesaEncryptedPassword = base64.b64encode(mpesaToEncryptPassword.encode())
        decodedPassword = mpesaEncryptedPassword.decode('utf-8')
        return  decodedPassword

genPassword()

def authenticator():
    r = requests.get(base_url + 'oauth/v1/generate?grant_type=client_credentials' ,auth=HTTPBasicAuth(consumer_Key, consumer_secret))

    return r.json()['access_token']

authenticator()