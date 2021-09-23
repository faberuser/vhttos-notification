from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import FirefoxOptions

import json, config, traceback, threading, os, logging
import time as timer
from datetime import datetime
from bs4 import BeautifulSoup

from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage

logging.basicConfig(
    handlers=[logging.FileHandler("./log.log", "a", "utf-8")],
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

viber = Api(BotConfiguration(
    name=config.NAME,
    avatar=config.AVATAR_URL,
    auth_token=config.TOKEN
))

def process(recipient_id:str):
    text = ('preparing task for user '+recipient_id)
    logging.info(text)
    options = FirefoxOptions()
    options.add_argument("--headless")
    try:
        driver = webdriver.Firefox(executable_path='./geckodriver')
    except OSError:
        driver = webdriver.Firefox(executable_path='./geckodriver.exe')
    except:
        driver = webdriver.Firefox(options=options, executable_path='./geckodriver')
    driver.get("https://vhttos.com/login")
    try:
        driver, recipient_id, usr, pwd = login(driver, recipient_id)
        task(driver, recipient_id, usr, pwd)
    except:
        pass

def login(driver, recipient_id):
    # get forms
    forms = driver.find_elements_by_class_name('input-form-reg')

    with open('./users.json', encoding="utf-8") as j:
        data = json.load(j)[recipient_id]
    usr =  data['username']
    pwd = data['password']
    try:
        # enter username
        username = forms[0]
        username.clear()
        username.send_keys(usr)

        # enter password
        password = forms[1]
        password.clear()
        password.send_keys(pwd)

        timer.sleep(10)

        # click login
        driver.find_element_by_css_selector('.btn-vhttech').click()

        timer.sleep(5)

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.foreach-temp')))
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.vht-badge-chip')))
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.riglist .row-implement')))
        
        return driver, recipient_id, usr, pwd
    except KeyboardInterrupt:
        driver.close()
        return
    except:
        send(recipient_id, 'Đăng nhập bị lỗi (sai email hoặc mật khẩu), vui lòng đăng ký lại')
        return

def task(driver, recipient_id, usr, pwd):
    text = (recipient_id+ ' up')
    logging.info(text)
    text = ('broke task for user '+recipient_id)
    try:
        refresh_count = 0
        while True:
            if refresh_count == 300:
                driver.refresh()
                timer.sleep(10)
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.foreach-temp')))
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.vht-badge-chip')))
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.riglist .row-implement')))
                refresh_count = 0
            try:
                with open('./users.json', encoding="utf-8") as j:
                    data = json.load(j)[recipient_id]
                max_temp = data['temp']
                if data['username'] != usr:
                    logging.info(text)
                    break
                elif data['password'] != pwd:
                    logging.info(text)
                    break
            except:
                traceback.print_exc()
                logging.info(text)
                break
            try:
                miner = None
                elements = driver.find_elements_by_css_selector('.riglist .row-implement')
                for element in elements:
                    css = element.value_of_css_property('background-color')
                    if css.startswith('rgba'):
                        rgb = css[5:][:-1].replace(',', '').split()
                    else:
                        rgb = css[4:][:-1].replace(',', '').split()
                    down = False
                    if len(rgb) == 3:
                        if rgb[0] != '41' or rgb[1] != '40' or rgb[2] != '40':
                            if rgb[0] != '34' or rgb[1] != '34' or rgb[2] != '34':
                                down = True
                    elif len(rgb) == 4:
                        if rgb[0] != '62' or rgb[1] != '99' or rgb[2] != '114' or rgb[3] != '0.3':
                            down = True
                    if down == True:
                        ele_source = element.get_attribute('innerHTML')
                        miner_ = BeautifulSoup(str(ele_source), 'html.parser').find('span', {'class': 'vht-badge-chip rig-name nv-row'})
                        if miner is None:
                            miner_ = BeautifulSoup(str(ele_source), 'html.parser').find('span', {'class': 'vht-badge-chip rig-name rx-row'})
                        miner = miner_.get_text()
                        time = get_current_time(datetime.now())
                        message = f'Máy đào {miner} của bạn đang rớt mạng vào lúc {time}! https://vhttos.com/rig-list'
                        text = (recipient_id+': '+message)
                        logging.info(text)
                        send(recipient_id, message)

                html = driver.page_source
                riglist = BeautifulSoup(html, 'html.parser').find_all('div', {'class': 'container-fluid riglist'})[4]
                rigs = BeautifulSoup(str(riglist), 'html.parser').find_all('div', {'class': 'row row-implement'})
                for rig in rigs:
                    status = BeautifulSoup(str(rig), 'html.parser').find('div', {'class': 'col-lg-4 col-md-5 col-sm-5 col-12 nomarpad'})
                    temps_ = BeautifulSoup(str(status), 'html.parser').find_all('div', {'class': 'foreach-temp'})
                    temps = []
                    for temp_ in temps_:
                        temps.append((temp_.get_text().replace('\n', '')).replace(' ', ''))
                    overheat = []
                    for temp in temps:
                        if int(temp) >= int(max_temp):
                            overheat.append(temp)
                    if overheat != []:
                        miner_ = BeautifulSoup(str(ele_source), 'html.parser').find('span', {'class': 'vht-badge-chip rig-name nv-row'})
                        if miner is None:
                            miner_ = BeautifulSoup(str(ele_source), 'html.parser').find('span', {'class': 'vht-badge-chip rig-name rx-row'})
                        miner_ = miner_.get_text()
                        if miner_ == miner:
                            continue
                        time = get_current_time(datetime.now())
                        message = f'Máy đào {miner_} của bạn có {len(overheat)} card đang quá {max_temp} độ vào lúc {time}! https://vhttos.com/rig-list'
                        text = (recipient_id+': '+message)
                        logging.info(text)
                        send(recipient_id, message)
            except:
                traceback.print_exc()
                pass
            timer.sleep(60)
            refresh_count += 60
        driver.close()
    except KeyboardInterrupt:
        driver.close()

def get_current_time(datetime_now):
    time = datetime.now().strftime("%H:%M %d/%m/%Y")
    return time

def send(id, text):
    viber.send_messages(id, [TextMessage(text=text)])

def main():
    with open('./users.json', encoding="utf-8") as j:
        data = json.load(j)
    for user in data:
        exist = False
        for thread in threading.enumerate(): 
            if thread.name == user:
                exist = True
        if exist == False:
            thread = threading.Thread(target=process, args=(user,))
            thread.name = user
            thread.start()
main()