import time
import requests  # pip install requests
import logging
import random

# window.Telegram.WebApp.initData
init_data = ''

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def recovery_energy(energy):
    recovery_time = 1000 - int(energy)

    logging.warning(f"Recovering energy {recovery_time}s")
    time.sleep(recovery_time)


if __name__ == '__main__':
    auth_response = requests.post(
        'https://server.questioncube.xyz/auth',
        json={
            'initData': init_data
        },
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'Referer': 'https://www.thecubes.xyz/'
        }
    )

    if auth_response.status_code != 200:
        logging.error(f'Auth request failed: {auth_response.text}')
        exit(1)

    user_data = auth_response.json()
    energy = user_data['energy']

    if user_data['banned_until_restore'] == 'true':
        recovery_energy(energy)

    while True:
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

        if mined_response.status_code != 200:
            if mined_response.text == '???????????????':
                logging.error(f'Too much requests')
                time.sleep(5)
                continue

            if mined_response.text == 'Not enough energy':
                recovery_energy(energy)
                continue

            logging.error(f'Mined request failed: {mined_response.text}')
            time.sleep(5)
            continue

        mined_data = mined_response.json()
        energy = mined_data['energy']

        logging.info(
            f"Mined: {mined_data['mined_count']}; Drops: {mined_data['drops_amount']}; Energy: {energy};")

        time.sleep(random.randint(4, 12))
