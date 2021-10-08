import logging, config, json, requests, time
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

viber = Api(BotConfiguration(
    name='VHTTOS Rig Notification',
    avatar=config.AVATAR_URL,
    auth_token=config.TOKEN
))

localhost_url = "http://localhost:4040/api/tunnels"
while True:
    time.sleep(5)
    try:
        tunnel_url = requests.get(localhost_url).text
        j = json.loads(tunnel_url)
        webhook_url = j['tunnels'][0]['public_url']
        viber.set_webhook(webhook_url)
        break
    except:
        pass