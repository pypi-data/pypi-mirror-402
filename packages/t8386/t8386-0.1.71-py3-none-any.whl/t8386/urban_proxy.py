import random
import time
import requests

from requests.models import Response

import json
from tenacity import retry, stop_after_attempt, wait_random, retry_if_not_exception_type

from aiohttp import (
    ClientSession,
    ClientTimeout,
    ContentTypeError,
    ClientConnectionError,
)

from t8386.logger import Logger

class UrbanProxyElement:
    username: str = None
    password: str = None
    creation_time: int = 0
    expiration_time: int = 0
    auth_str: str = ''
    ip: str = ''

    def __init__(self, data):
        self.data = data
        self.name = data['name']
        self.group = data['group']
        self.type = data['type']
        self.address = data['address']
        self.weight = data['weight']
        self.signature = data['signature']
        self.primary = data['address']['primary']
        self.host = data['address']['primary']['host']
        self.port = data['address']['primary']['port']
        self.ip = data['address']['primary']['ip']
        self.password = '1'

class UrbanProxyConfig:
    client_app_name = 'URBAN_VPN_BROWSER_EXTENSION'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,vi;q=0.7,cs;q=0.6,th;q=0.5',
        'authorization': 'Bearer wBgfw5JK1K24wpo01S5wSbtNi5MEIMjI',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'chrome-extension://eppiocemhmnlbhjplcgkofciiegomcon',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'none',
        'sec-fetch-storage-access': 'active',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
    }

    urls = {
        'access_token': 'https://api-pro.falais.com/rest/v1/security/tokens/accs',
        'get_proxy': 'https://api-pro.falais.com/rest/v1/security/tokens/accs-proxy',
        'get_proxy_list': 'https://stats.falais.com/api/rest/v2/entrypoints/countries',
    }


class UrbanProxy:

    proxy_list: list[UrbanProxyElement] = []
    proxy: UrbanProxyElement = None
    access_token: str = None

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(UrbanProxyConfig.headers)
       
    def refresh_session(self):
        self.session = requests.Session()
        self.session.headers.update(UrbanProxyConfig.headers)

    def get_access_token(self):
        response = self.session.post(UrbanProxyConfig.urls['access_token'], json={
            "type": "accs",
            'clientApp': {
                'name': UrbanProxyConfig.client_app_name
            }
        })
        if response.status_code == 200:
            self.access_token = response.json()['value']
            return self.access_token
        return None

    def handle_before_request(self):
        if not self.access_token:
            self.get_access_token()

    def is_expired(self, proxy: UrbanProxyElement):
        return proxy.expiration_time < int(time.time() * 1000)

    def handle_after_response(self, response: Response):
        if response.status_code == 401:
            self.refresh_session()
            self.get_access_token()
        elif response.status_code != 200:
            Logger.log_error(f"[UrbanProxy] Error: {response.status_code} - {response.text}")

            self.reset()


    def reset(self):
        self.proxy = None
        self.proxy_list = []
        self.access_token = None

    @retry(
        retry=retry_if_not_exception_type(
            (ContentTypeError, ClientConnectionError)),
        stop=stop_after_attempt(5),
        wait=wait_random(min=1, max=3)
    )
    def auth_proxy(self, proxy: UrbanProxyElement):
        self.handle_before_request()

        # print(f"Auth proxy: {proxy.host}:{proxy.port}")

        headers = {
            **UrbanProxyConfig.headers,
            'authorization': f'Bearer {self.access_token}',
            'x-client-app': UrbanProxyConfig.client_app_name,
        }

        body = {
            "type": "accs-proxy",
            "clientApp": {
                "name": UrbanProxyConfig.client_app_name
            },
            "signature": proxy.signature,
        }

        response = self.session.post(
            UrbanProxyConfig.urls['get_proxy'], data=json.dumps(body), headers=headers)
        if response.status_code != 200:
            self.handle_after_response(response)

            raise Exception(
                f'[UrbanProxy] Auth proxy failed -> {response.status_code} : {response.text}')

        resp = response.json()

        proxy.username = resp['value']
        proxy.creation_time = resp['creationTime']
        proxy.expiration_time = resp['expirationTime']
        proxy.auth_str = f"http://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"


        self.proxy_list.remove(proxy)

        self.proxy_list.append(proxy)

        proxy.ip = self.get_ip(proxy)

        return proxy

    def get_proxy(self, proxy: UrbanProxyElement = None):
            
        if len(self.proxy_list) == 0:
            proxy = None
            self.get_proxy_list()

        if proxy is not None:
            if self.is_expired(proxy) == False:
                return proxy

        element = random.choice(self.proxy_list)

        if not element:
            raise Exception('[UrbanProxy] Proxy not found')

        if element.expiration_time not in [0, None] and element.expiration_time > int(time.time() * 1000):
            return element


        return self.auth_proxy(element)

    def get_proxy_list(self):

        self.handle_before_request()

        headers = {
            **UrbanProxyConfig.headers,
            'authorization': f'Bearer {self.access_token}',
            'x-client-app': UrbanProxyConfig.client_app_name,
        }

        response = self.session.get(
            UrbanProxyConfig.urls['get_proxy_list'], headers=headers)
        
        if response.status_code != 200:
            self.handle_after_response(response)
            raise Exception(
                f'[UrbanProxy] Get proxy list failed -> {response.status_code} : {response.text}')

        resp = response.json()

        for country in resp['countries']['elements']:
            servers = country['servers']
            elements = servers['elements'] if 'elements' in servers else []
            for element in elements:
                self.proxy_list.append(UrbanProxyElement(element))

        Logger.log_success(f"[UrbanProxy] Proxy list available: {len(self.proxy_list)}")
        return self.proxy_list
    

    def get_ip(self, proxy: UrbanProxyElement):
        
        resp = requests.get('https://api.ipify.org', proxies={
            'https': proxy.auth_str
        }, timeout=10)

        return resp.text

# if __name__ == '__main__':
#     urban_proxy = UrbanProxy()

#     for i in range(5):
#         proxy = urban_proxy.get_proxy()

#         print(proxy.auth_str)
