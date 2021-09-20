from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
import logging, config, json, threading, traceback, crawler

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name=config.NAME,
    avatar=config.AVATAR_URL,
    auth_token=config.TOKEN
))

sub_help = 'Nếu muốn đăng ký, vui lòng nhắn tin theo cú pháp:\n\nDK EMAIL MẬT_KHẨU NHIỆT_ĐỘ\n\nTrong đó:\n'+\
        'EMAIL: Email đăng nhập của bạn trên VHTTOS.\nMẬT_KHẨU: Mật khẩu đăng nhập của bạn trên VHTTOS.\nNHIỆT_ĐỘ: Khi có card bằng hoặc hơn nhiệt độ này sẽ thông báo.\n\n'+\
        'Nếu muốn hủy vui lòng nhắn: HUY'
sub_suc = 'Đăng ký thành công'
sub_fail = 'Đăng ký thất bại, vui lòng nhắn tin theo đúng cú pháp'
sub_unsub = 'Hủy đăng ký thành công'

@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message
        # lets echo back
        msg = message.text
        if msg.lower().startswith('dk'):
            info = msg.split()
            if len(info) > 4 or len(info) < 4:
                send_message(viber_request.sender.id, sub_fail)
                return "Error"
            elif info[3].isnumeric() == False:
                send_message(viber_request.sender.id, 'Đăng ký thất bại, nhiệt độ phải là 1 số tự nhiên')
                return "Error"
            try:
                with open('./users.json', encoding="utf-8") as j:
                    data = json.load(j)
                data[viber_request.sender.id] = {
                    "username": info[1],
                    "password": info[2],
                    "temp": int(info[3]),
                    "name": viber_request.sender.name
                }
                with open('users.json', 'w', encoding="utf-8") as j:
                    json.dump(data, j, indent=4)
                exist = False
                for thread in threading.enumerate():
                    if thread.name == viber_request.sender.id:
                        exist = True
                if exist == False:
                    thread = threading.Thread(target=crawler.process, args=(viber_request.sender.id,))
                    thread.name = viber_request.sender.id
                    thread.start()
                send_message(viber_request.sender.id, sub_suc)
            except:
                traceback.print_exc()
                send_message(viber_request.sender.id, sub_fail)
        elif msg.lower().startswith('huy'):
            with open('./users.json', encoding="utf-8") as j:
                    data = json.load(j)
            try:
                del data[viber_request.sender.id]
                with open('users.json', 'w', encoding="utf-8") as j:
                    json.dump(data, j, indent=4)
                send_message(viber_request.sender.id, sub_unsub)
            except:
                send_message(viber_request.sender.id, 'Không tìm thấy thông tin đăng ký nào của bạn trong cơ sở dữ liệu')
        else:
            send_message(viber_request.sender.id, sub_help)

    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_mepost_requestssages(viber_request.get_user.id, [
            TextMessage(text="thanks for subscribing!")
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

def send_message(id, text):
    viber.send_messages(id, [TextMessage(text=text)])

@app.route('/pa/set_webhook', methods=['GET'])
def webhook():
    return Response(status=200)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
