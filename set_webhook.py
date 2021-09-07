import logging, config
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

webhook_url = str(input('enter webhook url: '))
viber.set_webhook(webhook_url)