from cfg import *
import requests
import json
import datetime
import telebot
import time
from time import sleep
from telebot import types
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import threading
import pprint
import re
import traceback
import subprocess
import shlex
import socket
import os
import telebot
import telnetlib
import ipaddress
import sqlite3
import ast
import pyautogui
import pyscreeze
import psutil







bot = telebot.TeleBot(token)



'''ПИШЕМ ЛОГ ОШИбОК И ТП'''
def log(text):
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")  # Исправлено на %S для секунд
    with open('botlog.log', 'a+') as file:
        file.write(f'\n{formatted_time} - {text}')  # Используем отформатированное время

log(text="бот был успешно запущен")

"""СТАТУС ПОДПИСКИ"""
def remind_status(date_str):
    # Преобразуем строку в объект datetime
    target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    current_date = datetime.datetime.now()

    # Вычисляем разницу между целевой датой и текущей
    time_difference = target_date - current_date

    # Определяем статус на основе разницы во времени
    if time_difference > datetime.timedelta(days=180):  # больше 6 месяцев
        return '✅'
    elif datetime.timedelta(days=30) < time_difference <= datetime.timedelta(
            days=180):  # меньше 6 месяцев и больше месяца
        return '⚠️'
    else:  # меньше месяца
        return '❌'


"""ИЗ ДАТЫ ФОРМАТА ДД.ММ.ГГГГ в ГГГГ-ММ-ММ"""
def dd_mm_yyyy_to_yyyy_mm_dd(date_str):
    # Разделяем строку по точкам
    day, month, year = date_str.split('.')
    # Формируем новую строку в нужном формате
    return f"{year}-{month}-{day}"



"""АПТАЙМ ГЛАВНОГО СЕРВЕРА"""
def getmainserveruptime():
    zabbix_url = zabbixurl
    zabbix_user = zabbix_log
    zabbix_password = zabbix_pass
    headers = {'Content-Type': 'application/json-rpc'}
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": zabbix_user,
            "password": zabbix_password
        },
        "id": 1
    }
    auth_token = requests.post(zabbix_url, headers=headers, data=json.dumps(data)).json()["result"]

    hostid = requests.post(zabbix_url, headers=headers, data=json.dumps({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [
                    "ALPHA"

                ]
            }
        },
        "auth": auth_token,
        "id": 1
    })).json()["result"][0]["hostid"]
    data_element = requests.post(zabbix_url, headers=headers, data=json.dumps({
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "hostids": hostid,
        },
        "id": 3,
        "auth": auth_token
    })).json()["result"]
    for i in data_element:
        if i['name'] == 'Windows: Uptime':
            unix_time = int(i['lastvalue'])

            readable_time = datetime.datetime.fromtimestamp(unix_time)

            # Íà÷àëî Unix ýïîõè
            epoch_start = datetime.datetime(1970, 1, 1)

            # Âû÷èñëÿåì ðàçíèöó
            time_difference = readable_time - epoch_start

            # Ïîëó÷àåì êîëè÷åñòâî äíåé, ÷àñîâ è ìèíóò
            days = time_difference.days
            seconds = time_difference.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60

            # Ôîðìàòèðóåì ðåçóëüòàò
            result = f"{days} дня, {hours} часов, {minutes} минут"
            return result



"""АПТАЙМ УСТРОЙСТВА ГДЕ ХОСТИТСЯ БОТ"""
def get_uptime():
    # Получаем время загрузки системы
    boot_time = psutil.boot_time()
    # Преобразуем время загрузки в datetime
    boot_time = datetime.datetime.fromtimestamp(boot_time)
    # Получаем текущее время
    current_time = datetime.datetime.now()
    # Рассчитываем аптайм
    uptime = current_time - boot_time
    return uptime



"""ПОГОДА ГОРОДА КОТОРЫЙ ХОТИМ"""
def weather():
    req = requests.get(f"http://api.weatherapi.com/v1/current.json?key={weatherapitoken}&q={city}").json()
    temp = int(req["current"]["temp_c"])
    text = f"Погода в {cityindex}: {temp} °C"
    if temp <= 0:
        text = f"Погода в {cityindex}: {temp} °C ❄️"
    if temp > 0 and temp <= 20:
        text = f"Погода в {cityindex}: {temp} °C 🌤️"
    if temp >= 20:
        text = f"Погода в {cityindex}: {temp} °C ☀️"
    return text






"""ДЛЯ НАПОМИНАНИЙ ВЫЧЕСЛЯЕМ ДАТУ КОГДА НУЖНО МЕССЕДЖ ПРЕСЛАТЬ"""
def calculate_reminder_date(start_date_str, subscription_duration, reminder_time):
    # Преобразуем строку даты в объект datetime
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')

    # Определяем длительность подписки
    duration_mapping = {
        "1 день": 1,
        "3 дня": 3,
        "1 неделя": 7,
        "3 месяца": 90,
        "6 месяцев": 180,
        "12 месяцев": 365,
        "2 года": 730,
        "3 года": 1095
    }

    if subscription_duration in duration_mapping:
        end_date = start_date + datetime.timedelta(days=duration_mapping[subscription_duration])
    else:
        raise ValueError("Недопустимая длительность подписки")

    # Определяем время для напоминания
    reminder_mapping = {
        "1 месяц": 30,
        "2 недели": 14,
        "3 дня": 3
    }

    if reminder_time in reminder_mapping:
        reminder_date = end_date - datetime.timedelta(days=reminder_mapping[reminder_time])
    else:
        raise ValueError("Недопустимое время для напоминания")

    # Возвращаем дату в нужном формате
    return f"{reminder_date.strftime('%Y-%m-%d')}"












"""IP КАЛЬКУЛЯТОР"""
def get_network_info(ip, subnet_mask):
    # Создаем объект сети на основе IP и маски
    network = ipaddress.ip_network(f"{ip}/{subnet_mask}", strict=False)

    # Получаем адрес сети
    network_address = str(network.network_address)
    # Получаем CIDR
    cidr = network.prefixlen
    # Получаем первый доступный адрес
    first_available = str(network.network_address + 1)
    # Получаем последний доступный адрес
    last_available = str(network.broadcast_address - 1)
    # Получаем количество адресов в диапазоне
    num_addresses = network.num_addresses - 2  # Исключаем адрес сети и широковещательный

    # Формируем текстовый формат
    result = (
        f"Адрес сети: {network_address}\n"
        f"Маска: {str(network.netmask)}\n"
        f"CIDR: {cidr}\n"
        f"Первый доступный адрес диапазона: {first_available}\n"
        f"Последний доступный адрес диапазона: {last_available}\n"
        f"Количество адресов в диапазоне: {num_addresses}"
    )

    return result



def get_current_time():
    now = datetime.datetime.now()  # получаем текущее время
    return now.strftime("%H:%M:%S")  # форматируем время в строку
"""NSLOOKUP ДОМЕННОГО ИМЕНИ"""
def nslookup(domain):
    try:
        # Получаем IP-адреса для указанного домена
        ip_addresses = socket.gethostbyname_ex(domain)
        return ip_addresses[2]  # Возвращаем список IP-адресов
    except socket.gaierror as e:
        log(f"Ошибка: {e}")
        return f"Ошибка: {e}"


"""ПО TELNET ПРОВЕРЯЕМ ОТКРЫТ ЛИ ПОРТ"""
def check_port(ip, port):
    try:
        # Устанавливаем таймаут в 5 секунд
        tn = telnetlib.Telnet(ip, port, timeout=5)
        tn.close()
        return f"IP-адрес: {ip} Порт: {port} ✅"
    except Exception as e:
        return f"IP-адрес: {ip} Порт: {port} ❌"
"""ПУТЬ ДО IP"""
def tracert(ip_address):
    try:
        # Выполнение команды tracert
        result = subprocess.run(['tracert', ip_address], capture_output=True, text=True)

        # Проверка на ошибки
        if result.returncode == 0:
            return result.stdout.encode('windows-1251', errors='replace').decode('cp866', errors='replace')
        else:
            return f"Ошибка: {result.stderr}"
   # Вывод ошибки
    except Exception as _ex:
        log(f"Произошла ошибка: {_ex}")
        return f"Произошла ошибка: {_ex}"




"""ПИНГ ХОСТА"""
def ping(host):
    if "in" in host:
        host = get_ip(host)
        if host is None:
            return None

    command = f"ping -n 4 {host}"  # Используем -c для указания количества пакетов
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = process.communicate(timeout=100)

    output_decoded = output.decode('cp866')
    return output_decoded





"""ПРЕОБРАЗУЕТ НАСТОЯЩЕЕ ВРЕМЯ В ФОРМАТ ЧИСЛО НАВЗАНИЕ МЕСЯЦА ХХ:ХХ"""
def current_time_jata():
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    dt = datetime.datetime.now()
    day = dt.day
    month = months[dt.month - 1]  # Индексация месяцев начинается с 0
    year = dt.year
    hour = dt.hour
    minute = dt.minute

    return f"{day} {month} {year} {hour:02}:{minute:02}"

"""ПРЕОБРАЗУЕТ UNIX ВРЕМЯ В ФОРМАТ ЧИСЛО НАВЗАНИЕ МЕСЯЦА ХХ:ХХ"""
def unix_to_jata(unix_time):
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    dt = datetime.datetime.fromtimestamp(int(unix_time))
    day = dt.day
    month = months[dt.month - 1]  # Индексация месяцев начинается с 0
    year = dt.year
    hour = dt.hour
    minute = dt.minute

    return f"{day} {month} {year} {hour:02}:{minute:02}"


"""UNIX ВО ВРЕМЯ ДЛЯ ЗАПРОСОВ К АРХИВУ MACROSCOP"""
def unix_to_formatted_time(unix_time):
    # Преобразуем Unix-время в объект datetime
    dt_object = datetime.datetime.fromtimestamp(int(unix_time))
    # Вычитаем 20 минут
    dt_object -= datetime.timedelta(minutes=20)
    # Форматируем объект datetime в нужный формат
    formatted_time = dt_object.strftime("%d.%m.%Y %H:%M:%S")
    return formatted_time




"""ВОЗВРАЩАЕТ ПРОБЛЕМЫ ИЗ ZABBIX
В ФОРМАТЕ
{ИМЯ ХОСТА:[ВРЕМЯ В UNIX , НАЗВАНИЕ ПРОБЛЕМЫ]}"""
def get_problems_from_zabbix():
    zabbix_url = zabbixurl
    zabbix_user = zabbix_log
    zabbix_password = zabbix_pass

    headers = {'Content-Type': 'application/json-rpc'}
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": zabbix_user,
            "password": zabbix_password
        },
        "id": 1
    }
    auth_token = requests.post(zabbix_url, headers=headers, data=json.dumps(data)).json()["result"]
    try:
        groupid = requests.post(zabbix_url, headers=headers, data=json.dumps({
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend",
                "filter": {
                    "name": [
                        hostgroup_for_problems
                    ]
                }
            },
            "auth": auth_token,
            "id": 1
        })).json()["result"][0]["groupid"]
        hostids = list()
        hosts = requests.post(zabbix_url, headers=headers, data=json.dumps({
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "groupids": [groupid]
            },
            "auth": auth_token,
            "id": 1
        })).json()["result"]
        for hostdescription in hosts:
            hostid = hostdescription["hostid"]
            hostids.append(hostid)

        problems = requests.post(zabbix_url, headers=headers, data=json.dumps({
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "selectHosts": "extend",
                "hostids": hostids,

            },

            "auth": auth_token,
            "id": 1
        })).json()["result"]
        eventids = list()
        for i in problems:
            eventids.append(i["eventid"])
        events = requests.post(zabbix_url, headers=headers, data=json.dumps({
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "selectHosts": "extend",
                "eventids": eventids,

            },

            "auth": auth_token,
            "id": 1
        })).json()["result"]

        readylist_key = list()

        for info in events:
            # print(info)

            for hostlist in info["hosts"]:
                readylist_key.append(hostlist["host"])



        readylist_object = list()
        for i in problems:
            list_of_values = [i["clock"],i["name"]]

            readylist_object.append(list_of_values)

        alllist = dict(zip(readylist_key, readylist_object))
        alllist = dict(reversed(alllist.items()))
        return alllist


    except Exception as _ex:
        log(_ex)
        traceback.print_exc()
        print(_ex)



"""IP АДРЕС ПО ZABBIX ИМЕНИ"""
def get_ip(host):
    zabbix_url = zabbixurl
    zabbix_user = zabbix_log
    zabbix_password = zabbix_pass
    headers = {'Content-Type': 'application/json-rpc'}
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": zabbix_user,
            "password": zabbix_password
        },
        "id": 1
    }
    auth_token = requests.post(zabbix_url, headers=headers, data=json.dumps(data)).json()["result"]

    groupid = requests.post(zabbix_url, headers=headers, data=json.dumps({
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": "extend",
            "filter": {
                "name": [
                    "Matrix-Home_Group"
                ]
            }
        },
        "auth": auth_token,
        "id": 1
    })).json()["result"][0]["groupid"]

    hostids = list()
    hosts = requests.post(zabbix_url, headers=headers, data=json.dumps({
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "selectInterfaces": ['ip', 'port', 'dns'],
            "groupids": [groupid]

        },
        "auth": auth_token,
        "id": 1
    })).json()["result"]
    for i in hosts:
        if i["host"] == host:
            return i["interfaces"][0]["ip"]
    return None

mainbot_menu = ""
"""/START ВЫДАЕМ КНОПКИ"""
@bot.message_handler(func=lambda message: message.text == "/start" or message.text == comeback)
def start(message):
    global mainbot_menu
    log(f"{message.from_user.username} сделал /start")
    chat_id = message.chat.id
    text = f"<b>Вы открыли главное меню</b> "
    mainbot_menu = types.ReplyKeyboardMarkup()
    button_network_map = types.KeyboardButton(network_map)
    button_cameras_List = types.KeyboardButton(cameraslist)
    button_tools = types.KeyboardButton(tools)
    button_reminds = types.KeyboardButton(reminders)
    button_files = types.KeyboardButton(files)
    button_list = types.KeyboardButton(commands_list)
    mainbot_menu.row(button_network_map)
    mainbot_menu.row(button_cameras_List,button_files)
    mainbot_menu.row(button_tools)
    mainbot_menu.row(button_reminds,button_list)
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, text, reply_markup=mainbot_menu, parse_mode="HTML")
        sentd = bot.send_message(chat_id, "-------",)
        try:
            with open('pinnedmessageinfo.txt', 'r') as file:
                file = file.readlines()
                bot.delete_message(file[1], file[0])
        except Exception as _ex:
            log(_ex)
            pass

        with open('pinnedmessageinfo.txt', 'w') as file:
            file.write(f'{sentd.message_id}\n{sentd.chat.id}')

        bot.pin_chat_message(chat_id=message.chat.id, message_id=sentd.id)
        threading.Thread(target=pinnedmessage, args=(chat_id, sentd.message_id)).start()
    else:
        log(f"{message.from_user.username} сделал /start но он отсутвует среди зарегистрированных пользователей")

def pinnedmessage(chat_id,message_id, ):
    while True:
        sleep(120)
        texts = f"{weather()}|ALPHA uptime: {getmainserveruptime()}"
        bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=texts)


"""ИДЕНТИИКАТОР ПОТОКА ПО ИМЕНИ В MACROSCOP"""
def get_channel_id(camera_name):
    req = requests.get(f"http://10.9.8.4:8080/configex?login={macroscop_log}&password={macroscop_pass}&responsetype=json")

    for allinfo_about_device in req.json()["Channels"]:
        if camera_name == allinfo_about_device["Name"]:
            return allinfo_about_device["Id"]
    return "Нет такой камеры"




"""КАДР ИЗ КАМЕРЫ И ИНФА О НЕЙ"""
@bot.message_handler(func=lambda message: "🎞️" in message.text)
def send_realtime_camera(message):
    log(f"{message.from_user.username} запросил камеру {button_zabbix_name[message.text]}")
    chat_id = message.chat.id
    zabbix_name = button_zabbix_name[message.text]
    macroscop_name = button_macroscop_name[message.text]
    cam_caption = (f"<b>Имя камеры</b>: {macroscop_name}\n"
                     f"<b>IP-адрес камеры</b> {get_ip(zabbix_name)}\n")
    channelid = get_channel_id(macroscop_name)

    if zabbix_name in get_problems_from_zabbix().keys():
        cam_caption += (f"<b>Статус камеры</b>: ⛔ Камера не отвечает\n"
                        f"<b>Дата и время кадра</b>: {unix_to_jata(get_problems_from_zabbix()[zabbix_name][0])}\n"
                        )
        online = False
        macro_time = unix_to_formatted_time(get_problems_from_zabbix()[zabbix_name][0])


        req = requests.get(

         f"http://10.9.8.4:8080/site?login={macroscop_log}&password={macroscop_pass}&channelid={channelid}&withcontenttype=true&mode=archive&starttime={macro_time}&resolutionx=640&resolutiony=480")
    else:
        cam_caption += (f"<b>Статус камеры</b>: ✅ ОК\n"
                        f"<b>Дата и время кадра</b>: {current_time_jata()}")
        online = True
        req = requests.get(
              f"http://10.9.8.4:8080/site?login={macroscop_log}&password={macroscop_pass}&channelid={channelid}&withcontenttype=true&mode=realtime&&resolutionx=640&resolutiony=480")

    with open(f"{zabbix_name}.jpg", "wb") as file:
        file.write(req.content)
    with open(f"{zabbix_name}.jpg", "rb") as file:
        if str(chat_id) in whocanusebot:
            bot.send_photo(photo=file, chat_id=chat_id, caption=cam_caption, parse_mode="HTML")
            
            

        






"""ПЕРЕМЕЩЕНИЕ В МЕНЮ КАМЕР"""
@bot.message_handler(func=lambda message: message.text == cameraslist )
def move_to_cameraslist(message):
    log(f"{message.from_user.username} переместился в меню камер")
    chat_id = message.chat.id
    text = "<b>Вы переместились в список камер</b>"
    cameras_menu = types.ReplyKeyboardMarkup()
    button_entrance = types.KeyboardButton(cam_entrance)
    button_childrens = types.KeyboardButton(cam_childrens)
    button_yard = types.KeyboardButton(cam_yard)
    button_kidsprofi = types.KeyboardButton(cam_kidsprofi)
    button_comeback  = types.KeyboardButton(comeback)
    cameras_menu.row(button_entrance,button_childrens)
    cameras_menu.row(button_yard, button_kidsprofi)
    cameras_menu.row(button_comeback)

    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, text, reply_markup=cameras_menu, parse_mode="HTML")
    else:
        log(f"{message.from_user.username} переместился в меню камер но он отсутвует среди зарегистрированных пользователей")


"""ПЕРЕМЕЩЕНИЕ В МЕНЮ ИНСТРУМЕНТЫ"""
@bot.message_handler(func=lambda message: message.text == tools )
def move_to_tools(message):
    log(f"{message.from_user.username} переместился в меню инструментов")
    chat_id = message.chat.id
    text = "<b>Вы переместились в меню инструментов</b>"
    tools_menu = types.ReplyKeyboardMarkup()
    button_ping = types.KeyboardButton(ping_s)
    button_ping_t = types.KeyboardButton(ping_t)
    button_nslookup = types.KeyboardButton(nslookup_1)
    button_tracert = types.KeyboardButton(tracer_t)
    button_telnet = types.KeyboardButton(telnet)
    button_ip_calculator = types.KeyboardButton(ipcalc)
    button_comeback  = types.KeyboardButton(comeback)
    tools_menu.row(button_ping,button_ping_t)
    tools_menu.row( button_tracert,button_telnet)
    tools_menu.row(button_nslookup,button_ip_calculator)
    tools_menu.row(button_comeback)
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, text, reply_markup=tools_menu, parse_mode="HTML")
    else:
        log(f"{message.from_user.username} переместился в меню инструментов но он отсутвует среди зарегистрированных пользователей")


"""ПИНГУЕМ ХОСТ"""
@bot.message_handler(func=lambda message: message.text == ping_s)
def welcome_ip(message):
    log(f"{message.from_user.username} использовал команду пинг")
    chat_id = message.chat.id
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, "Что пинговать ? (IP-адрес/имя узла)")
        bot.register_next_step_handler(mesg, sendping)
    else:

        log(f"{message.from_user.username} переместился попытался пингануть но он отсутвует среди зарегистрированных пользователей")
        return None



def sendping(message):
    pings = str(ping(message.text))

    if "4 received" in pings or "получено = 4" in pings:
        pings = (f"Статус хоста - ✅OK\n-----------------------\n"
                 f"{pings}")
    elif "100% packet loss" in pings or "100% потерь" in pings :
        pings = (f"Статус хоста - ❌ Хост не отвечает\n-----------------------\n"
                 f"{pings}")
    elif pings == "":
        bot.send_message(message.chat.id, 'Пинг данного IP адреса/хоста невозможен.')
    else:
        pings = (f"Статус хоста - ⚠️ Обнаружены потери пакетов\n-----------------------\n{pings}")
    bot.send_message(message.chat.id, pings)

ip_calc = ""
subnet_mask = ""

@bot.message_handler(func=lambda message: message.text == ipcalc)
def welcone_ipcalc(message):
    chat_id = message.chat.id
    global ip_calc
    global subnet_mask
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, "<b>Введите IP-Адрес</b>:",
                                parse_mode="HTML")
        log(f"{message.from_user.username} использовал ip-калькулятор")
        bot.register_next_step_handler(mesg, how_ip)
    else:

        log(f"{message.from_user.username} переместился попытался ипользовать ip-калькулятор но он отсутвует среди зарегистрированных пользователей")
        return None

def how_ip(message):
    chat_id = message.chat.id
    global ip_calc
    global subnet_mask
    ip_calc = message.text
    mesg = bot.send_message(chat_id, "<b>Введите маску</b>:",
                            parse_mode="HTML")
    bot.register_next_step_handler(mesg,send_net_info)
def send_net_info(message):
    chat_id = message.chat.id
    global ip_calc
    global subnet_mask
    subnet_mask = message.text
    net_status = get_network_info(ip_calc,subnet_mask)
    bot.send_message(chat_id,net_status)








"""ПОСТАВИТЬ НА ПИНГ"""
@bot.message_handler(func=lambda message: message.text == ping_t)
def start_ping(message):
    chat_id = message.chat.id
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(message.chat.id, "Что пинговать ? (IP-адрес/номер камеры/имя узла)"
                                                 "")
        log(f"{message.from_user.username} использовал поставить на пинг")
        bot.register_next_step_handler(mesg, pinging)
    else:

        log(f"{message.from_user.username} переместился попытался ипользовать поставить на пинг но он отсутвует среди зарегистрированных пользователей")
        return None

def pinging(message):
    if "in" in message.text:
        pingname = get_ip(message.text)
    else:
        pingname = message.text


    mesg = bot.send_message(message.chat.id,text=f"Поставил на пинг {message.text}\n"
                                                 f"Буду пинговать 2 часа \n"
                                      f"Как только узел станет доступен,я сразу сообщу в чат!")
    if pingname == None:
        bot.edit_message_text(chat_id=mesg.chat.id, message_id=mesg.id,
                              text=f"Узла {message.text} не существует ")
    time = 0
    pings = ping(message.text)
    if pings == "" :
        mesg = bot.edit_message_text(chat_id=mesg.chat.id, message_id=mesg.id,
                                     text=f"Узла {message.text} не существует ")
        checkping = True
    else:
        checkping = False

    while time < 7200 and checkping == False :
        pings = ping(pingname)

        if ("4 received" in pings or "3 received" in pings or "2 received" in pings or "1 received" in pings) and time < 30 or ("получено = 4" in pings or "получено = 3" in pings or "получено = 2" in pings or "получено = 1" in pings) and time < 30:
            mesg = bot.edit_message_text(chat_id=mesg.chat.id, message_id=mesg.id,
                                         text=f"Узел {message.text} пингуется уже сейчас! ✅\n"
                                              f"-----------------\n"
                                              f"{pings}")
            pinged = True
            break
        elif ("4 received" in pings or "3 received" in pings or "2 received" in pings or "1 received" in pings) and time > 30 or ("получено = 4" in pings or "получено = 3" in pings or "получено = 2" in pings or "получено = 1" in pings) and time > 30:
            mesg = bot.edit_message_text(chat_id=mesg.chat.id, message_id=mesg.id,
                                         text=f"Узел {message.text} начал пинговаться! ✅\n"
                                              f"-----------------\n"
                                              f"{pings}")
            pinged = True
            break
        elif "100% packet loss" in pings or "100% потерь" in pings:
            pings = (f"Статус хоста - ❌ Хост не отвечает\n-----------------------\n"
                     f"{pings}")
        else:
            pings = (f"Статус хоста - ⚠️ Обнаружены потери пакетов\n-----------------------\n{pings}")
        time += 10
        sleep(10)
    if pinged != True:
        mesg = bot.edit_message_text(chat_id=mesg.chat.id, message_id=mesg.id,
                                    text=f"Узел {message.text} так и не запинговался! Я пинговал целых 3 часа")





"""TRACERT ДО IP"""
@bot.message_handler(func=lambda message: message.text == tracer_t)
def welcome_tracert(message):
    chat_id = message.chat.id

    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id, "<b>К чему хотите получить маршрут</b> ? (IP-адрес/Имя узла)",
                                parse_mode="HTML")
        bot.register_next_step_handler(mesg, sendtracert)
        log(f"{message.from_user.username} использовал tracer_t")
    else:

        log(f"{message.from_user.username} переместился попытался ипользовать tracert но он отсутвует среди зарегистрированных пользователей")
        return None
ip = ""
port = ""

def sendtracert(message):
    chat_id = message.chat.id
    text = f"Путь до {message.text}\n{tracert(message.text)}"
    bot.send_message(chat_id=chat_id,text=text,)

"""TELNET ПРОВЕРЯЕМ ДОСТУПНОСМТЬ ПОРТА"""
@bot.message_handler(func=lambda message: message.text == telnet)
def welcone_telnet(message):
    log(f"{message.from_user.username} использовал telnet")
    chat_id = message.chat.id
    global ip
    global port
    mesg = bot.send_message(chat_id, "<b>Введите IP-Адрес</b>:",
                           parse_mode="HTML")
    bot.register_next_step_handler(mesg, how_port)
def how_port(message):
    chat_id = message.chat.id
    global ip
    global port
    ip = message.text
    mesg = bot.send_message(chat_id, "<b>Введите порт</b>:",
                            parse_mode="HTML")
    bot.register_next_step_handler(mesg, send_port_status)
def send_port_status(message):
    chat_id = message.chat.id
    global ip
    global port
    port = message.text
    port_status = check_port(ip,port)
    bot.send_message(chat_id,port_status)




"""NSLOOKUP """
@bot.message_handler(func=lambda message: message.text == nslookup_1)
def what_domain_name(message):
    log(f"{message.from_user.username} использовал nslookup")
    chat_id = message.chat.id
    text = "<b>Введите имя домена:</b>"

    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(mesg, sendnslookup)
        log(f"{message.from_user.username} использовал nslookup")
    else:
        log(f"{message.from_user.username} переместился попытался ипользовать nslookup но он отсутвует среди зарегистрированных пользователей")
        return None

def sendnslookup(message):
    chat_id = message.chat.id
    text = (f"<b>IP-адреса  для {message.text}</b>:\n{nslookup(message.text)}")
    mesg = bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")


"""ПЕРЕМЕЩЕНИЕ В МЕНЮ ФАЙЛЫ"""
@bot.message_handler(func=lambda message: message.text == files )
def move_to_files(message):
    log(f"{message.from_user.username} переместился в меню файлов")
    chat_id = message.chat.id
    text = "<b>Вы переместились в меню файлов</b>"
    files_menu = types.ReplyKeyboardMarkup()
    button_download = types.KeyboardButton(download_file)
    button_upload_file = types.KeyboardButton(upload_file)
    button_delete_file = types.KeyboardButton(delete_file)


    button_comeback  = types.KeyboardButton(comeback)
    files_menu.row(button_download,button_upload_file)
    files_menu.row(button_delete_file)
    files_menu.row(button_comeback)
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML",reply_markup=files_menu)

        log(f"{message.from_user.username} переместился в меню файлов")
    else:
        log(f"{message.from_user.username} попытался переместиться в меню файлов но он отсутвует среди зарегистрированных пользователей")
        return None




"""ПЕРЕМЕЩАЕМСЯ В РАБОЧУЮ ДИРЕКТОРИЮ И ЖДЕМ ОТВЕТА ОТ ПОЛЬЗОВАТЕЛЯ ЧТОБ ОН СКАЧАЛ ФАЙЛ"""
@bot.message_handler(func=lambda message: message.text == download_file)
def move_to_files_downloads(message):
    log(f"{message.from_user.username} скачал файл")
    files = []
    chat_id = message.chat.id
    files += os.listdir(path_to_files)
    text = (f"<b>Вы переместились в рабочую директорию</b>\n")
    for i in files:
        text += f"\n{i}\n"
    mesg = bot.send_message(chat_id, text, parse_mode="HTML")
    question_text = "<b>Введите имя файла для загрузки</b>:"

    mesg = bot.send_message(chat_id,question_text,parse_mode="HTML")
    bot.register_next_step_handler(mesg,sendfile)



"""ШЛЕМ ПОЛЬЗОВАТЕЛЮ ФАЙЛ"""
def sendfile(message):
    filename = message.text
    chat_id = message.chat.id
    try:
        bot.send_document(chat_id, open(fr"{path_to_files}\{filename}", "rb"))

    except Exception as _ex:
        log(_ex)
        text = "<b>Неверное имя файла</b>"
        bot.send_message(chat_id, text,parse_mode="HTML")





"""ПЕРЕМЕЩАЕМСЯ В РАБОЧУЮ ДИРЕКТОРИЮ И ЖДЕМ ОТВЕТА ОТ ПОЛЬЗОВАТЕЛЯ ЧТОБ ОН УДАЛИЛ ФАЙЛ"""
@bot.message_handler(func=lambda message: message.text == delete_file)
def move_to_files(message):
    log(f"{message.from_user.username} удалил файл")
    files = []
    chat_id = message.chat.id
    files += os.listdir(path_to_files)
    text = (f"<b>Вы переместились в рабочую директорию</b>\n")

    for i in files:
        text += f"\n{i}\n"
    mesg = bot.send_message(chat_id, text, parse_mode="HTML")
    question_text = "<b>Введите имя файла для удаления</b>:"

    if str(chat_id) in whocanusebot:

        mesg = bot.send_message(chat_id, question_text, parse_mode="HTML")
        bot.register_next_step_handler(mesg, deletefile)
        log(f"{message.from_user.username} переместился в меню файлов")
    else:

        log(f"{message.from_user.username} попытался удалить файл но он отсутвует среди зарегистрированных пользователей")
        return None



"""УДАЛЯЕМ ФАЙЛ ИЗ ДИРЕКТОРИИ"""
def deletefile(message):
    filename = message.text
    chat_id = message.chat.id
    text = f"Файл <b>{filename}</b> был удален"
    try:
        os.remove(fr"{path_to_files}\{filename}")
        bot.send_message(chat_id, text, parse_mode="HTML")

    except:
        text = "<b>Неверное имя файла</b>"
        bot.send_message(chat_id, text,parse_mode="HTML")




"""ЗАПРАШИВАЕМ ФАЙЛ У ПОЛЬЗОВАТЕЛЯ"""
@bot.message_handler(func=lambda message: message.text == upload_file)
def ask_for_file(message):
    log(f"{message.from_user.username} загрузил файл")
    chat_id = message.chat.id
    text = "<b>Пришлите файл</b>"
    bot.send_message(chat_id, text,parse_mode="HTML")



"""ЖДЕМ ФАЙЛ"""
@bot.message_handler(content_types=['document'])
def handle_document(message):
    log(f"{message.from_user.username} загрузил файл")
    chat_id = message.chat.id
    text = "<b>Файл успешно загружен</b>"
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Укажите путь, куда вы хотите сохранить файл
    file_path = os.path.join(path_to_files, message.document.file_name)

    # Создаем папку, если её нет
    if not os.path.exists(path_to_files):
        os.makedirs(path_to_files)

    # Сохраняем файл
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    bot.send_message(chat_id, "Файл успешно загружен.",parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == reminders)
def move_to_reminds_menu(message):
    log(f"{message.from_user.username} переместился в меню напоминаний")
    chat_id = message.chat.id
    text = "<b>Вы переместились в меню напоминаний</b>"
    files_menu = types.ReplyKeyboardMarkup()
    button_allreminds = types.KeyboardButton(all_reminds)
    button_new_remind = types.KeyboardButton(add_remind)
    button_delete_remind = types.KeyboardButton(delete_remind)

    button_comeback = types.KeyboardButton(comeback)
    files_menu.row(button_allreminds)
    files_menu.row(button_delete_remind, button_new_remind)
    files_menu.row(button_comeback)
    if str(chat_id) in whocanusebot:

        mesg = bot.send_message(chat_id=chat_id, text=text, reply_markup=files_menu, parse_mode="HTML")
        log(f"{message.from_user.username} переместился в напоминаний")
    else:

        log(f"{message.from_user.username} попытался удалить файл но он отсутвует среди зарегистрированных пользователей")
        return None

remind_name = ''
remindstart = ''
remind_duration = ''
when_toremind = ''
@bot.message_handler(func=lambda message: message.text == add_remind)
def move_to_reminds_menu(message):
    log(f"{message.from_user.username} добавил напоминание")
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind



    chat_id = message.chat.id
    text = "<b>Введите имя подписки</b>"
    mesg = bot.send_message(chat_id,text, parse_mode="HTML")
    bot.register_next_step_handler(mesg,question_date)



@bot.callback_query_handler(func=lambda call: call.data == "add_remind")
def deleteremind(call: types.CallbackQuery):
    log(f"{call.message.from_user.username} добавил напоминание")
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind



    chat_id = call.message.chat.id
    text = "<b>Введите имя подписки</b>"
    mesg = bot.send_message(chat_id,text, parse_mode="HTML")
    bot.register_next_step_handler(mesg,question_date)


@bot.message_handler(func=lambda message: message.text == add_remind)
def move_to_reminds_menu(message):
    log(f"{message.from_user.username} добавил напоминание")
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind



    chat_id = message.chat.id
    text = "<b>Введите имя подписки</b>"
    mesg = bot.send_message(chat_id,text, parse_mode="HTML")
    bot.register_next_step_handler(mesg,question_date)

def question_date(message):
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind
    msg_text = message.text
    remind_name = msg_text




    chat_id = message.chat.id
    text = "Введите дату оформления подписки в формате <b>ДД.ММ.ГГГГ</b>:"
    mesg = bot.send_message(chat_id, text, parse_mode="HTML")
    bot.register_next_step_handler(mesg, question_duration)


def question_duration(message):
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind
    chat_id = message.chat.id
    text = "<b>Выберите длительность подписки:</b>"
    msg_text = message.text

    remindstart = dd_mm_yyyy_to_yyyy_mm_dd(msg_text)
    try:
        # Пытаемся распарсить строку в дату
        datetime.datetime.strptime(remindstart, '%Y-%m-%d')
    except ValueError:
        text = "<b>Неверная дата введите еще раз</b>"
        mesg = bot.send_message(chat_id, text, parse_mode="HTML",)
        bot.register_next_step_handler(mesg, question_duration)
        return None
    remind_duration_menu = types.ReplyKeyboardMarkup()
    button_3month = types.KeyboardButton("3 месяца")
    button_6month = types.KeyboardButton("6 месяцев")
    button_12month = types.KeyboardButton("12 месяцев")
    button_2year = types.KeyboardButton("2 года")
    button_3year = types.KeyboardButton("3 года")
    button_1day = types.KeyboardButton("1 день")
    button_3day = types.KeyboardButton("3 дня")
    button_1week = types.KeyboardButton("1 неделя")

    remind_duration_menu.row(button_1day,button_3day,button_1week,button_3month)
    remind_duration_menu.row(button_6month, button_12month, button_2year, button_3year)
    mesg = bot.send_message(chat_id, text, parse_mode="HTML",reply_markup=remind_duration_menu)
    bot.register_next_step_handler(mesg, question_whenremind)


def question_whenremind(message):
    global remind_name
    global remindstart
    global remind_duration
    global when_toremind

    msg_text = message.text
    remind_duration = msg_text

    chat_id = message.chat.id
    text = "<b>За сколько до окончания подписки напомнить о необходимости продления?</b>:"
    remind_duration_menu = types.ReplyKeyboardMarkup()
    button_1month = types.KeyboardButton("1 месяц")
    button_2weeks = types.KeyboardButton("2 недели")
    button_3day = types.KeyboardButton("3 дня")
    remind_duration_menu.row(button_1month,button_2weeks,button_3day)
    mesg = bot.send_message(chat_id, text, parse_mode="HTML",reply_markup=remind_duration_menu)
    bot.register_next_step_handler(mesg, save_all)

def save_all(message):
    chat_id = message.chat.id

    global remind_name
    global remindstart
    global remind_duration
    global when_toremind
    msg_text = message.text
    when_toremind = msg_text
    mainbot_menu = types.ReplyKeyboardMarkup()
    button_network_map = types.KeyboardButton(network_map)
    button_cameras_List = types.KeyboardButton(cameraslist)
    button_tools = types.KeyboardButton(tools)
    button_reminds = types.KeyboardButton(reminders)
    button_files = types.KeyboardButton(files)
    button_list = types.KeyboardButton(commands_list)
    mainbot_menu.row(button_network_map)
    mainbot_menu.row(button_cameras_List, button_files)
    mainbot_menu.row(button_tools)
    mainbot_menu.row(button_reminds, button_list)

    remind_date = f"{calculate_reminder_date(remindstart,remind_duration,when_toremind)} 10:00"
    text = (f"Подписка добавлена:\n"
            f"Имя подписки <b>{remind_name}</b>\n"
            f"Дата оформления <b>{remindstart}</b>\n"
            f"Длительность подписки <b>{remind_duration}</b>\n"
            f"Напомнить за : <b>{when_toremind}</b>\n")


    mesg = bot.send_message(chat_id, text, parse_mode="HTML",reply_markup=mainbot_menu)
    with open("reminds.txt","a+", encoding='utf-8') as file:
        file.write(f"{[remind_name,remindstart,remind_duration,when_toremind,remind_date,chat_id]}\n")


"""ВСЕ НАПОМИНАНИЯ"""
@bot.message_handler(func = lambda message: message.text == all_reminds)
def getallreminds(message):
    log(f"{message.from_user.username} посмотрел все напоминания")
    text = "<b>Ваши подписки:</b>\n"
    chat_id = message.chat.id
    reminds_markup = types.InlineKeyboardMarkup()
    new_remind = types.InlineKeyboardButton(text=add_remind,callback_data="add_remind")
    del_remind = types.InlineKeyboardButton(text=delete_remind, callback_data="delete_remind")
    reminds_markup.row(new_remind,del_remind)
    with open ("reminds.txt" ,"r",encoding="utf-8") as file:
        for line in file:
            line = ast.literal_eval(line)
            text += f"\n<b>Статус</b> :{remind_status(line[4])} / Подписка на <b>{line[0]}</b>  <b>{line[2]}</b>  / оформлена <b>{line[1]}</b> /  напомню за <b>{line[3]}</b>\n---------------------"
    mesg = bot.send_message(chat_id, text,parse_mode="HTML",reply_markup=reminds_markup)


"""УДАЛИТЬ НАПОМИНАНИЕ РЕПЛИ КНОПКОЙ """
@bot.message_handler(func = lambda message: message.text == delete_remind)
def deleteremindreminds(message):
    log(f"{call.message.from_user.username} удалил напоминание")
    text = "<b>Ваши подписки:</b>\n"
    chat_id = message.chat.id
    with open("reminds.txt", "r", encoding="utf-8") as file:
        for line in file:
            line = ast.literal_eval(line)
            text += f"\nПодписка на <b>{line[0]}</b> / <b>{line[2]}</b>  / напомню за <b>{line[3]}</b>\n---------------------"
    mesg = bot.send_message(chat_id, text, parse_mode="HTML")
    mesg = bot.send_message(chat_id, "Введите название подписки для удаления:", parse_mode="HTML")
    bot.register_next_step_handler(mesg , funcdeleteremind)

"""УДАЛИТЬ НАПОМИНАНИЕ ИНЛАЙН КНОПКОЙ """
@bot.callback_query_handler(func=lambda call: call.data == "delete_remind")
def deleteremind(call: types.CallbackQuery):
    log(f"{call.message.from_user.username} удалил напоминание")
    text = "<b>Ваши подписки:</b>\n"
    chat_id = call.message.chat.id
    with open("reminds.txt", "r", encoding="utf-8") as file:
        for line in file:
            line = ast.literal_eval(line)
            text += f"\nПодписка на <b>{line[0]}</b> / <b>{line[2]}</b>  / напомню за <b>{line[3]}</b>\n---------------------"
    mesg = bot.send_message(chat_id, text, parse_mode="HTML")
    mesg = bot.send_message(chat_id, "Введите название подписки для удаления:", parse_mode="HTML")
    bot.register_next_step_handler(mesg , funcdeleteremind)


def funcdeleteremind(message):
    chat_id = message.chat.id
    msg_text = message.text
    list = []
    with open("reminds.txt", "r", encoding="utf-8") as file:
        for line in file:
            line = ast.literal_eval(line)
            list.append(line)
        for sub in list:
            if sub[0] == msg_text:

                list.remove(sub)
        with open("reminds.txt", "w", encoding="utf-8") as file:
            for newsub in list:
                file.write(f"{newsub}\n")
        bot.send_message(chat_id,text=f"Подписка {msg_text} была удалена")



def check_reminds():
    while True:
        now = datetime.datetime.now()  # Получаем текущее время и дату
        current_date_time = now.strftime("%Y-%m-%d %H:%M")
        with open("reminds.txt" ,"r+" , encoding="utf-8",errors='ignore') as file :
            for line in file:
                line = ast.literal_eval(line)
                if current_date_time == line[4]:
                    bot.send_message(chat_id=line[5], text=f"Подписка на {line[0]} заканчивается через: {line[3]}")
                    sleep(60)


threading.Thread(target=check_reminds).start()


@bot.message_handler(func = lambda message: message.text == commands_list)
def say_commands(message):

    chat_id = message.chat.id
    text = ("/get_problems – список всех проблем из заббикс\n"
            "/get_weather – покажет погоду в Энгельсе\n"
            "/get_screen – покажет полный скриншот ВМ бота\n"
            "/show_bot_uptime – покажет аптайм виртуалки с ботом\n"
            "/get_alpha_uptime – покажет аптайм главного сервера\n"
            "/get_doc – выплюнет файл с техдокументацией\n"
            "/get_log – покажет лог файл бота\n"
            "/reboot – перезагрузит виртуалку с ботом\n"
            "/about – покажет инфу о боте\n"
            "/get_keys - список ключей")
    bot.send_message(chat_id, text)
    log(f"{message.from_user.username} посмотрел список команд")


@bot.message_handler(commands = ["get_problems"])
def send_problems_from_zabbix(message):

    chat_id = message.chat.id
    problems = get_problems_from_zabbix()
    problemscount = 0
    probl = ""
    for i in problems.keys():
        problemscount +=1
        probl += f"Устройство: <b>{i}</b>\n"
        probl += (f"{problems[i][1]}\n"
                 f"Недоступно с: <b>{unix_to_jata(problems[i][0])}</b>\n"
                 f"----------------\n")
    text = f"Проблем в Zabbix <b>{problemscount}</b>\n\n"
    text += probl
    if str(chat_id) in whocanusebot:
        bot.send_message(chat_id, text,parse_mode="HTML")
        log(f"{message.from_user.username} посмотрел проблемы из zabbix")


@bot.message_handler(commands  =["get_weather"])
def send_weatherofcity(message):

    chat_id = message.chat.id
    text = weather()
    if str(chat_id) in whocanusebot:
        bot.send_message(chat_id, text)
        log(f"{message.from_user.username} посмотрел погоду")

@bot.message_handler(commands = ["get_screen"])
def desktop_send(message):

    chat_id = message.chat.id
    myScreenshot = pyautogui.screenshot()

    myScreenshot.save(r'desktop.png')
    with open("desktop.png", "rb") as desktop:
        if str(chat_id) in whocanusebot:
            bot.send_photo(chat_id,
                           photo=desktop)
            log(f"{message.from_user.username} посмотрел скриншот стола")

@bot.message_handler(func=lambda message: message.text == network_map)
def desktop_send(message):

    chat_id = message.chat.id
    myScreenshot = pyautogui.screenshot(region=(20,90, 1150,885))

    myScreenshot.save(r'desktop.png')
    with open("desktop.png", "rb") as desktop:
        if str(chat_id) in whocanusebot:
            bot.send_photo(chat_id,
                           photo=desktop)
            log(f"{message.from_user.username} посмотрел скриншот стола")

@bot.message_handler(commands = ["show_bot_uptime"])
def send_uptime(message):

    chat_id = message.chat.id
    text = str(get_uptime())[0:8]
    if str(chat_id) in whocanusebot:
        bot.send_message(chat_id, text)
        log(f"{message.from_user.username} посмотрел аптайм бота")

@bot.message_handler(commands = ["get_alpha_uptime"])
def send_uptime(message):

    chat_id = message.chat.id
    text = getmainserveruptime()
    if str(chat_id) in whocanusebot:
        bot.send_message(chat_id, text)
        log(f"{message.from_user.username} посмотрел аптайм главного сервера")

@bot.message_handler(commands = ["get_log"])
def logsend(message):
    chat_id = message.chat.id
    if str(chat_id) in whocanusebot:
        bot.send_document(chat_id,document=open("botlog.log"))
        log(f"{message.from_user.username} посмотрел лог файл бота ")
@bot.message_handler(commands = ["about"])
def logsend(message):
    chat_id = message.chat.id
    if str(chat_id) in whocanusebot:
        bot.send_document(chat_id,document=open("about.txt"))
        log(f"{message.from_user.username} посмотрел about ")


@bot.message_handler(commands=["get_keys"])
def logsend(message):
    chat_id = message.chat.id
    text = ""
    with open("keys.txt", "r") as file:
        for i in file:
            text += f"{i}\n"
        bot.send_message(chat_id,text)
    log(f"{message.from_user.username} посмотрел файл с ключами  ")
@bot.message_handler(commands=["reboot"])
def logsend(message):
    chat_id = message.chat.id
    if str(chat_id) in whocanusebot:
        mesg = bot.send_message(chat_id,'Введите пароль')
        bot.register_next_step_handler(mesg,reset)

def reset(message):
    if message.text == "Trustno1!@#":
        os.system("shutdown /r /t 0")


while True:

    try:
        bot.polling(none_stop=True)
    except Exception as _ex:
        log(_ex)
        traceback.print_exc()

        print(_ex)

#endofcode