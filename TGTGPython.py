import http.client
import json
import sys
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import time


baseUrl = ""
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "en-US",
    "Accept-Charset": "utf-8"
}
with open('config.json') as logs:
    config = json.load(logs)


def recupTokens():
    email = config['email']
    password = config['password']
    authURL = "https://apptoogoodtogo.com/api/auth/v1/loginByEmail"
    jsonToPost = {
        'device_type': 'UNKNOWN',
        'email': email,
        'password': password
    }
    response = requests.post(authURL, json=jsonToPost, headers=headers)
    data = json.loads(response.text)
    config['access_token'] = data['access_token']
    config['refresh_token'] = data['refresh_token']
    config['user_id'] = data['startup_data']['user']['user_id']
    with open('config.json', 'w') as config_json:
        json.dump(config, config_json, indent=4)
    listFav(config['user_id'], config['access_token'])


def listFav(user_id, access_token):
    favURL = "https://apptoogoodtogo.com/api/item/v4/"
    bearerToken = f'Bearer {access_token}'
    headersUser = {
        "User-Agent": "TGTG/19.12.0 (724) (Android/Unknown; Scale/3.00)",
        "Authorization": bearerToken
    }
    jsonToPost = {
        "favorites_only": True,
        "origin": {
            "latitude": 52.5170365,
            "longitude": 13.3888599
        },
        "radius": 200,
        "user_id": user_id
    }
    response = requests.post(favURL, json=jsonToPost,
                             headers=headersUser)
    data = json.loads(response.text)
    paniersText = []
    for item in data['items']:
        nameRestaurant = item['display_name']
        nbrePanier = item['items_available']
        print(f'{nameRestaurant} : {nbrePanier} panier(s) disponible(s)')
        if(nbrePanier > 0):
            paniersText.append(
                f'Il y a {nbrePanier} panier disponible à {nameRestaurant}')
    if len(paniersText) > 0:
        sendMail(paniersText)
    time.sleep(600)
    listFav(user_id, access_token)


def sendMail(paniersText):
    gmail_user = config['mail']['gmail_user']
    gmail_password = config['mail']['gmail_password']
    receveir = config['mail']['mailReceiver']
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = receveir
    msg['Subject'] = 'Paniers Disponibles!'
    body = '\n'.join(paniersText)
    body = MIMEText(body)
    msg.attach(body)
    server.login(gmail_user, gmail_password)
    server.sendmail(gmail_user, receveir, msg.as_string())
    server.close()


if __name__ == '__main__':
    recupTokens()
