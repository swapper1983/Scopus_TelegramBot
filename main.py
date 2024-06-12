"""Подгружаем необходимые библиотеки."""
# import requests
import json
import os
from datetime import datetime  # , timedelta

import telebot
from dotenv import load_dotenv
from telebot import types

from data import (doctype_cmd, excl_regions_mes, greeting_mes, period_cmd,
                  regions_cmd, regions_menu)
from scopus_api import apikey_validation, pub_counts

load_dotenv()

# Импортируем скрытые переменные
secret_token: str = os.getenv('TOKEN')
# api_key: str = os.getenv('API_KEY')
api_key_list: json = json.loads(os.environ['API_KEY_LST'])
# secret_chat_id: str = os.getenv('CHAT_ID')

# Переменные для работы
date_format: str = '%d/%m/%Y, %H:%M'
time_format: str = '%H:%M'  # '%d-%m-%Y, %H:%M'
coff: int = 100
# valid_key: str = apikey_validation(api_key_list)
# ar_cmd: str = 'DOCTYPE(ar) AND '
# re_cmd: str = 'DOCTYPE(re) AND '
# cp_cmd: str = 'DOCTYPE(cp) AND '
# ar_re_cp_cmd: str = ' DOCTYPE(ar OR re OR cp) AND '

# Настраиваем телерамм-бота
bot = telebot.TeleBot(token=secret_token)


def metrics_calc(region_ru: str, period: str) -> dict:
    """Функция обращения к Scopus за расчётом метрик."""
    query_response: dict = {}
    russia_rate: dict = {}
    region_en: str = list(filter(lambda x:
                                 regions_menu[x] == region_ru,
                                 regions_menu))[0]
    query_period: str = period_cmd[period]
    query_region: str = regions_cmd[region_en]
    query_russia: str = regions_cmd['Russia']
    for type, query_doctype in doctype_cmd.items():
        valid_key: str = apikey_validation(api_key_list)
        query = query_doctype + query_period + query_region
        query_response[type] = pub_counts(valid_key, query)
        query_ru = query_doctype + query_period + query_russia
        russia_rate[type] = pub_counts(valid_key, query_ru)
    return query_response, russia_rate


def message_func(response_info: tuple) -> str:
    """Функция формирования сообщения для отправки в телеграм."""
    reg_metric, rus_metric = response_info
    tm = datetime.now().strftime(date_format)
    rus_ar_rate: float = round(int(reg_metric['ar']) /
                               int(rus_metric['ar']) *
                               coff, 3)
    rus_re_rate: float = round(int(reg_metric['re']) /
                               int(rus_metric['re']) *
                               coff, 3)
    rus_cp_rate: float = round(int(reg_metric['cp']) /
                               int(rus_metric['cp']) *
                               coff, 3)
    reg_sum = (int(reg_metric['ar']) +
               int(reg_metric['re']) +
               int(reg_metric['cp']))
    rus_sum = (int(rus_metric['ar']) +
               int(rus_metric['re']) +
               int(rus_metric['cp']))
    reg_sum_rate: float = round(reg_sum / rus_sum * coff, 3)
    mes = (f"{region_ru}, данные за {period}:\n\n"
           f"🟢 Научных статей: {reg_metric['ar']} ед. ({rus_ar_rate}%)\n"
           f"🟢 Научных обзоров: {reg_metric['re']} ед. ({rus_re_rate}%)\n"
           f"🟢 Материалов конференций: {reg_metric['cp']} ед. ({rus_cp_rate}%)\n\n"
           f"Итого в сумме: {reg_sum} ед. ({reg_sum_rate}%)\n\n"
           f"Дата и время запроса: {tm}\n")
    return mes


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Функция входа, обработки команды start от пользователя."""
    name = message.chat.first_name
    bot.send_message(chat_id=message.chat.id, text=greeting_mes.format(name))
    user_markup = regions_menu_markup()
    mes = 'Выберите субъект для измерения:'
    bot.send_message(chat_id=message.chat.id, text=mes,
                     reply_markup=user_markup)


@bot.message_handler(content_types=['text'])
def handle_regions_menu_click(message):
    """Функция обработки нажатий кнопок (выбор региона)."""
    user_markup = years_menu_markup()
    global region_ru
    region_ru = message.text
    mes = 'Выберите период измерения:'
    if region_ru in list(regions_menu.values()):
        bot.send_message(chat_id=message.chat.id, text=mes,
                         reply_markup=user_markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_period_menu_click(call):
    """Функция обработки нажатий кнопок (выбор периода)."""
    global period
    period = call.data
    print(call.message.chat.first_name, call.message.chat.id,
          region_ru, call.data, datetime.now().strftime(date_format))
    if period in period_cmd:
        try:
            metrics = metrics_calc(region_ru, period)
            mes = message_func(metrics)
        except:
            mes = excl_regions_mes
    bot.send_message(call.message.chat.id, text=mes)


def regions_menu_markup():
    """Функция подготовки меню (выбор региона)."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, value in regions_menu.items():
        button_text = value
        button = types.KeyboardButton(text=button_text)
        keyboard.add(button)
    return keyboard


def years_menu_markup():
    """Функция подготовки меню (выбор периода)."""
    buttons_columns = 3
    buttons_added = []
    markup = types.InlineKeyboardMarkup(row_width=buttons_columns)
    for index, key in enumerate(period_cmd):
        button_text = key
        button_callback = key
        buttons_added.append(types.InlineKeyboardButton(
            text=button_text, callback_data=button_callback))
    markup.add(*buttons_added)
    return markup


if __name__ == '__main__':
    # bot.polling()
    bot.infinity_polling()
