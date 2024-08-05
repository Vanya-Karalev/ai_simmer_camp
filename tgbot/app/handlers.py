import os
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiofiles
import ssl
from aiohttp import ClientSession, TCPConnector
from app.generators import gpt4, transcribe_audio, text_to_speech

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
    file_name = None
    audio_file_path = None
    try:
        # Get the file info from Telegram
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

        # Generate GPT-4 response
        response = await gpt4(transcription)
        gpt_text = response.choices[0].message.content
        await message.answer(gpt_text)

        audio_file_path = await text_to_speech(gpt_text)
        audio_file = FSInputFile(audio_file_path)

        await message.answer_voice(audio_file)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await message.answer(f"An error occurred: {e}")
    finally:
        await state.clear()
        if file_name and os.path.exists(file_name):
            os.remove(file_name)
        if audio_file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)
