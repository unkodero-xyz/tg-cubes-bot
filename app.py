import time
import requests  # pip install requests
import logging
import random
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class Worker(threading.Thread):
    def __init__(self, id, init_data):
        super(Worker, self).__init__()
        self.id = id
        self.init_data = init_data

    def recovery_energy(self, energy):
        recovery_time = 1000 - int(energy)

        logging.warning(f"[{self.id}] Recovering energy {recovery_time}s")
        time.sleep(recovery_time)

    def run(self):
        auth_response = requests.post(
            'https://server.questioncube.xyz/auth',
            json={
                'initData': self.init_data
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
                'Referer': 'https://www.thecubes.xyz/'
            }
        )

        if auth_response.status_code != 200:
            logging.error(f'[{self.id}] Auth request failed: {auth_response.text}')
            return

        user_data = auth_response.json()
        energy = user_data['energy']

        if user_data['banned_until_restore'] == 'true':
            self.recovery_energy(energy)

        while True:
            try:
                mined_response = requests.post(
                    'https://server.questioncube.xyz/game/mined',
                    json={
                        'token': user_data['token']
                    },
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
                        'Referer': 'https://www.thecubes.xyz/'
                    }
                )
            except Exception as e:
                logging.error(f'[{self.id}] Mined request exception: {e}')
                time.sleep(10)
                continue

            if mined_response.status_code != 200:
                if mined_response.text == '???????????????':
                    logging.error(f'[{self.id}] Too much requests')
                    time.sleep(5)
                    continue

                if mined_response.text == 'Not enough energy':
                    self.recovery_energy(energy)
                    continue

                logging.error(f'[{self.id}] Mined request failed: {mined_response.text}')
                time.sleep(5)
                continue

            mined_data = mined_response.json()
            energy = mined_data['energy']

            logging.info(f"[{self.id}] Mined: {mined_data['mined_count']}; Drops: {mined_data['drops_amount']}; Energy: {energy};")

            time.sleep(random.randint(4, 12))


if __name__ == '__main__':
    with open('init_data.txt', 'r') as init_data_file:
        line = 0
        for init_data in init_data_file:
            line += 1
            Worker(line, init_data.strip()).start()
