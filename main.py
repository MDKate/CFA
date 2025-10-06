# Импорт библиотек
import pandas as pd
import numpy as np
import sys
import logging
import asyncio
import os
import re
from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram import Router, F, Bot
from aiogram.types import FSInputFile
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
TOKEN_GROUP = os.getenv("TOKEN_GROUP")

# # Подключение к боту
# with open('token.txt', 'r') as file:
#     token_value = file.read().strip()
# os.environ['TELEGRAM_BOT_TOKEN'] = token_value
# TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Определяем диспетчер и перехватчик
dp = Dispatcher()
router = Router()
dp.include_router(router)

global structure

# Определяем ф-ию инициализации
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("hi")
    await dp.start_polling(bot)


# --------------------------------Словари-------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# async def read_dict():

global key_buttons_1rang, key_buttons_text, key_buttons_termins, key_all_opros

# Функция для инициализации/обновления словарей
def update_dictionaries():
    global key_buttons_1rang, key_buttons_text, key_buttons_termins, key_all_opros

    structure_f = pd.read_excel(os.path.abspath('structure.xlsx'), engine='openpyxl')

    # Инициализация key_buttons_1rang
    level, marker, text_messege, buttns = structure_f[structure_f['Уровень'] == 1].iloc[0]
    buttns = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]
    key_buttons_1rang = {}
    for i in buttns:
        key_buttons_1rang[i] = 2

    # Инициализация остальных словарей
    key_buttons_text = structure_f.set_index('Маркер')['Уровень'].to_dict()

    key_buttons_termins = structure_f[structure_f['Маркер'] == list(key_buttons_1rang.keys())[0]]['Кнопки'].iloc[0]
    key_buttons_termins = [btn.strip() for btn in key_buttons_termins.strip('[]').split(']\n[')]

    key_all_opros = list(key_buttons_1rang.keys()) + key_buttons_termins


# Вызов функции при старте для инициализации
update_dictionaries()



# --------------------------------Функции-------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
async def read_table(type_z, message):
    structure_f = pd.read_excel(os.path.abspath('structure.xlsx'), engine='openpyxl')
    if type_z == 1:
        level, marker, text_messege, buttns = structure_f[structure_f['Уровень'] == 1].iloc[0]
        return level, marker, text_messege, buttns
    elif type_z == 2:
        level, marker, text_messege, buttns = \
            structure_f[(structure_f['Уровень'] == 2) & (structure_f['Маркер'] == message.text)].iloc[0]
        return level, marker, text_messege, buttns
    elif type_z == 3:
        level, marker, text_messege, buttns = \
            structure_f[structure_f['Маркер'] == 'Получить консультацию по ЦФА'].iloc[0]
        return level, marker, text_messege, buttns
    elif type_z == 4:
        level, marker, text_messege, buttns = structure_f[structure_f['Маркер'] == message.text].iloc[0]
        return level, marker, text_messege, buttns
    elif type_z == 5:
        structure_f = structure_f[~structure_f['Маркер'].isin(key_all_opros)]
        level, marker, text_messege, buttns = structure_f[structure_f['Маркер'] == message.text].iloc[0]
        return level, marker, text_messege, buttns



# --------------------------------Загрузка структуры--------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
@dp.message(Command("update_table"))  # Начать обновление таблицы
async def send_me_message(message: Message, bot: Bot):
    await bot.send_message(
        chat_id=message.from_user.id,
        text="Отправьте файл в формате xlsx! Не меняйте его название!")


@dp.message(F.document)
async def doc_message(message: Message, bot: Bot):
    document = message.document
    if document.file_name and document.file_name.endswith('.xlsx'):
        try:
            destination = f"{document.file_name}"
            await bot.download(document, destination=destination)
            new_structure = pd.read_excel(destination, engine='openpyxl')
            structure = new_structure.copy()

            # Обновляем словари после загрузки нового файла
            update_dictionaries()

            await bot.send_message(chat_id=message.from_user.id, text="Таблица успешно обновлена!")
        except Exception as e:
            await bot.send_message(chat_id=message.from_user.id, text=f"Ошибка при обработке файла: {str(e)}")


# Используйте Command вместо F.text
@dp.message(Command("download"))
async def download_command(message: Message, bot: Bot):
    try:
        await bot.send_document(
            chat_id=message.from_user.id,
            document=FSInputFile(os.path.abspath('structure.xlsx'))
        )
    except Exception as e:
        await message.answer(f"Ошибка при отправке файла: {str(e)}")



# --------------------------------Обработчики---------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
@dp.message(CommandStart())  # Первый уровень
async def cmd_start1(message: Message, bot: Bot):
    level, marker, text_messege, buttns = await read_table(1, message)
    builder = ReplyKeyboardBuilder()
    buttns = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]
    for button_text in buttns:
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(1)

    await bot.send_message(
        chat_id=message.chat.id,
        text=text_messege,
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML
    )


@router.message(lambda message: message.text not in key_buttons_text.keys()) # Второй уровень - работа с текстом
async def fn_text(message: Message, bot: Bot):
    # with open('token_group.txt', 'r') as file:
    #     token_group = file.read().strip()
    username = message.from_user.username
    text_messege = f"Добрый день! \nВам поступил новый запрос по ЦФА от @{username} \nТекст запроса: <pre>{message.text}</pre>"
    await bot.send_message(
        chat_id=TOKEN_GROUP,
        text=text_messege, parse_mode=ParseMode.HTML)
    level, marker, text_messege, buttns = await read_table(3, message)

    await bot.send_message(
        chat_id=message.chat.id,
        text=buttns, parse_mode=ParseMode.HTML)



@router.message(lambda message: message.text in key_buttons_1rang.keys()) # Второй уровень
async def fn_1(message: Message, bot: Bot):
    internal_command = key_buttons_1rang[message.text]
    # print(message.text)

    level, marker, text_messege, buttns = await read_table(1, message)
    buttns_list = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]

    if internal_command == 2 and message.text != 'Получить консультацию по ЦФА':
        level, marker, text_messege, buttns = await read_table(2, message)
        builder = ReplyKeyboardBuilder()
        buttns = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]
        for button_text in buttns:
            builder.add(KeyboardButton(text=button_text))
        builder.add(KeyboardButton(text='/start'))
        builder.adjust(1)

        await bot.send_message(
            chat_id=message.chat.id,
            text=text_messege,
            reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)
    elif internal_command == 2 and message.text == 'Получить консультацию по ЦФА':
        level, marker, text_messege, buttns = await read_table(3, message)
        await bot.send_message(
            chat_id=message.chat.id,
            text=text_messege, parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text in key_buttons_termins) # Третий уровень ответы
async def fn_2(message: Message, bot: Bot):
    # print('key_buttons_termins = ', message.text)
    level, marker, text_messege, buttns = await read_table(4, message)
    # print(marker)
    builder = ReplyKeyboardBuilder()
    buttns = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]
    for button_text in buttns:
        builder.add(KeyboardButton(text=button_text))
    builder.add(KeyboardButton(text='/start'))
    builder.adjust(1)
    await bot.send_message(
        chat_id=message.chat.id,
        text=text_messege,
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)


@router.message(lambda message: message.text not in key_all_opros) # Третий уровень опрос
async def fn_3(message: Message, bot: Bot):
    # print('key_all_opros = ', message.text)
    level, marker, text_messege, buttns = await read_table(5, message)

    builder = ReplyKeyboardBuilder()
    buttns = [btn.strip() for btn in buttns.strip('[]').split(']\n[')]
    for button_text in buttns:
        builder.add(KeyboardButton(text=button_text))
    builder.add(KeyboardButton(text='/start'))
    builder.adjust(1)

    await bot.send_message(
        chat_id=message.chat.id,
        text=text_messege,
        reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)











if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())