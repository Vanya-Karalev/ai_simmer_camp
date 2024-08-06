import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
from config import settings

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def gpt4(question):
    try:
        # response = await client.chat.completions.create(
        #     messages=[{'role': 'user', 'content': str(question)}],
        #     model='gpt-4'
        # )
        # return response

        assistant = await client.beta.assistants.create(
            name="Telegram Assistant",
            instructions="Provide clear, concise, and engaging answers based only on the provided data.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4",
        )

        thread = await client.beta.threads.create()

        message = await client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=str(question)
        )

        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="Provide clear, concise, and engaging answers based only on the provided data."
        )

        if run.status == 'completed':
            messages = await client.beta.threads.messages.list(
                thread_id=thread.id
            )
            logger.info(f"msgs: {messages}")
            response = messages.data[0].content[0].text.value
            return response
        else:
            logger.error(f"Run status: {run.status}")
            return None
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
