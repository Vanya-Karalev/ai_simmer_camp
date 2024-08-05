import os
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiofiles
import ssl
from aiohttp import ClientSession, TCPConnector
from app.generators import gpt4, transcribe_audio

# Initialize the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class Generate(StatesGroup):
    text = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer('Добро пожаловать в бот! Напишите ваш запрос')
    await state.clear()


@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer('Подождите, ваш запрос все еще генерируется...')


@router.message(F.text)
async def generate(message: Message, state: FSMContext):
    await state.set_state(Generate.text)
    try:
        response = await gpt4(message.text)
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        await message.answer("An error occurred while generating the response.")
    finally:
        await state.clear()


@router.message(F.voice)
async def handle_voice(message: Message, state: FSMContext):
    file_id = message.voice.file_id
    try:
        file_info = await message.bot.get_file(file_id)
        file_path = file_info.file_path

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        file_name = f'voice_{message.message_id}.ogg'

        async with ClientSession(connector=TCPConnector(ssl=ssl_context)) as session:
            async with session.get(f'https://api.telegram.org/file/bot{os.getenv("TG_TOKEN")}/{file_path}') as resp:
                if resp.status == 200:
                    async with aiofiles.open(file_name, 'wb') as f:
                        await f.write(await resp.read())
                else:
                    logger.error(f"Failed to download file: {resp.status}")
                    await message.answer("Failed to download the voice message.")
                    return

        transcription = await transcribe_audio(file_name)
        await message.answer(transcription)
        response = await gpt4(transcription)
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await message.answer(f"An error occurred: {e}")
    finally:
        await state.clear()
        if os.path.exists(file_name):
            os.remove(file_name)
