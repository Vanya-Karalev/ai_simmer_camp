import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def gpt4(question):
    try:
        response = await client.chat.completions.create(
            messages=[{'role': 'user', 'content': str(question)}],
            model='gpt-4'
        )
        return response
    except Exception as e:
        logger.error(f"Error generating GPT-4 response: {e}")
        raise


async def transcribe_audio(file_path):
    try:
        with open(file_path, 'rb') as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        logger.info(f"Transcription response: {response}")

        transcription_text = response.text
        return transcription_text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise


async def text_to_speech(text: str) -> str:
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        logger.info(f"TTS response: {response}")

        file_path = "output.mp3"
        with open(file_path, "wb") as f:
            f.write(response.content)

        return file_path
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise
