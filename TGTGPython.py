import http.client
import json
import sys
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import time

baseUrl = "https://apptoogoodtogo.com/api"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "en-US"
}


def recupTokens():
    email = config['email']
    password = config['password']
    authURL = baseUrl + "/auth/v1/loginByEmail"
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
    return [config['access_token'], config['user_id']]


def listFav(tokens):
    favURL = baseUrl + "/item/v4/"
    bearerToken = f'Bearer {tokens[0]}'
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
        "user_id": tokens[1]
    }
    response = requests.post(favURL, json=jsonToPost,
                             headers=headersUser)
    data = json.loads(response.text)
    paniersText = []
    boolSend = False
    t = time.localtime()
    current_time = time.strftime("\nRapport à %H:%M:%S ", t)
    print(current_time)
    for item in data['items']:
        nameRestaurant = item['display_name']
        nbrePanier = item['items_available']
        idItem = item['item']['item_id']
        # S'il y a un changement, on envoie un mail
        if (idItem in items and items[idItem] != nbrePanier and nbrePanier != 0) or (idItem not in items and nbrePanier != 0):
            paniersText.append(
                f'Il y a {nbrePanier} panier(s) disponible(s) à {nameRestaurant}')
            boolSend = True
        items[idItem] = nbrePanier
        print(f'{nameRestaurant} : {nbrePanier} panier(s) disponible(s)')

    if boolSend and config['mail']['gmail_user'] != "":
        sendMail(paniersText)
    time.sleep(600)
    listFav(tokens)


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
    items = {}
    with open('config.json') as logs:
        config = json.load(logs)
    tokens = recupTokens()
    listFav(tokens)
