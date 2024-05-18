import datetime
import json
import os
import random
import time
import requests  # pip install requests
import logging
import threading
from urllib.parse import parse_qs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class Worker(threading.Thread):
    def __init__(self, id, init_data, proxy):
        super(Worker, self).__init__()
        self.id = id
        self.init_data = init_data
        self.proxy = proxy

        parsed_init_data = parse_qs(self.init_data, strict_parsing=True)
        user_data = json.loads(parsed_init_data['user'][0])

        if len(user_data['first_name']) > 0:
            self.full_name = user_data['first_name']

        if len(user_data['last_name']) > 0:
            if len(user_data['first_name']) > 0:
                self.full_name += ' '
            self.full_name += user_data['last_name']

    def recovery_energy(self, energy):
        recovery_time = 1000 - int(energy)

        logging.warning(f"[{self.id}] [{self.full_name}] Recovering energy {recovery_time}s")
        time.sleep(recovery_time)

    def run(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'Referer': 'https://www.thecubes.xyz/'
        }

        proxies = None
        if self.proxy is not None:
            proxies = {
                'http': self.proxy,
                'https': self.proxy
            }

        try:
            auth_response = requests.post(
                'https://server.questioncube.xyz/auth',
                json={
                    'initData': self.init_data
                },
                headers=headers,
                proxies=proxies
            )
        except Exception as e:
            logging.error(f'[{self.id}] [{self.full_name}] Auth request exception: {e}')
            time.sleep(10)
            return self.run()

        if auth_response.status_code != 200:
            logging.error(f'[{self.id}] [{self.full_name}] Auth request failed: {auth_response.text}')
            return

        user_data = auth_response.json()
        energy = int(user_data['energy'])
        drops_amount = int(user_data['drops_amount'])

        if user_data['banned_until_restore'] == 'true':
            self.recovery_energy(energy)

        while True:
            try:
                mined_response = requests.post(
                    'https://server.questioncube.xyz/game/mined',
                    json={
                        'token': user_data['token']
                    },
                    headers=headers,
                    proxies=proxies
                )
            except Exception as e:
                logging.error(f'[{self.id}] [{self.full_name}] Mined request exception: {e}')
                time.sleep(10)
                continue

            if mined_response.status_code != 200:
                if mined_response.text == '???????????????':
                    logging.error(f'[{self.id}] [{self.full_name}] Too much requests')
                    time.sleep(5)
                    continue

                if mined_response.text == 'Not enough energy':
                    now = datetime.datetime.now()
                    if not (drops_amount >= 500 and 2 <= now.hour <= 7):
                        self.recovery_energy(energy)
                        continue
                    else:
                        while drops_amount >= 500 and energy < 2000:
                            logging.warning(f'[{self.id}] [{self.full_name}] Buying energy')

                            try:
                                buy_response = requests.post(
                                    'https://server.questioncube.xyz/game/rest-proposal/buy',
                                    json={
                                        'token': user_data['token'],
                                        'proposal_id': 4
                                    },
                                    headers=headers,
                                    proxies=proxies
                                )

                                buy_data = buy_response.json()
                            except:
                                continue

                            energy = int(buy_data['energy'])
                            drops_amount = int(buy_data['drops_amount'])
                        continue

                if mined_response.text == '? banned ?':
                    self.recovery_energy(energy)
                    continue

                if mined_response.text == 'Token not found':
                    return self.run()

                logging.error(f'[{self.id}] [{self.full_name}] Mined request failed: {mined_response.text}')
                time.sleep(5)
                continue

            mined_data = mined_response.json()
            energy = int(mined_data['energy'])
            drops_amount = int(mined_data['drops_amount'])

            logging.info(
                f"[{self.id}] [{self.full_name}] Drops: {drops_amount}; Energy: {energy}; Boxes: {mined_data['boxes_amount']};")

            time.sleep(random.randint(5, 8))


if __name__ == '__main__':
    use_proxy = False

    if os.path.isfile('proxies.txt'):
        logging.info('Loading proxy')
        with open('proxies.txt') as proxies_file:
            proxies = proxies_file.readlines()
            use_proxy = True

    proxy_line = 0

    with open('init_data.txt', 'r') as init_data_file:
        line = 0
        for init_data in init_data_file:
            line += 1

            p = None
            if use_proxy:
                p = proxies[proxy_line].strip()

            Worker(line, init_data.strip(), p).start()

            if use_proxy:
                proxy_line +=1
                if len(proxies) <= proxy_line:
                    proxy_line = 0
