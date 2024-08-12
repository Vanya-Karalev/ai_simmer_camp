import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import UserValue
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


async def determine_value(user_input: str) -> str:
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI assistant designed to extract and identify core values or principles behind user statements. "
                    "Based on the nature of the user’s query, identify relevant values or principles such as learning, mathematics, self-improvement, etc. "
                    "If the value is not clear from the statement, respond with 'No clear value identified.'"
                )
            },
            {
                "role": "user",
                "content": f"User statement: {user_input}"
            },
            {
                "role": "assistant",
                "content": "Core value(s):"
            }
        ],
        functions=[
            {
                "name": "determine_user_values",
                "description": "Identify the core values or principles expressed in the user's statement. The response should include relevant values based on the context of the statement.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "statement": {
                            "type": "string",
                            "description": "The user's statement from which to extract core values.",
                        }
                    },
                    "required": ["statement"],
                },
            }
        ],
        function_call="auto"
    )

    return response.choices[0].message.content


async def check_value(value: str) -> bool:
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant skilled at identifying and validating core values "
                        "expressed in a user's statement. Based on the user's input, determine the "
                        "primary value or principle they are expressing, and validate it using the "
                        "provided validation tool."
                    )
                },
                {"role": "user", "content": f"User statement: {value}"},
                {"role": "assistant", "content": "Core value:"}
            ],
            functions=[
                {
                    "name": "validate_value",
                    "description": "Validate the identified value to ensure it is clear and meaningful.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "description": "The core value identified from the user's statement.",
                            }
                        },
                        "required": ["value"],
                    },
                }
            ],
            function_call="auto"
        )

        result = response.choices[0].message.content
        if result.lower() == "true":
            return True
        else:
            return False

    except Exception as e:
        raise Exception(f"Error saving value to the database: {e}")


async def save_value(user_input: str, user_id: int, session: AsyncSession) -> bool:
    try:
        value = await determine_value(user_input)

        is_valid = await check_value(value)
        if not is_valid:
            logger.error(f"Invalid value detected: {value}")
            return False

        user_value = UserValue(user_id=user_id, value=value)
        session.add(user_value)
        await session.commit()

        logger.info(f"Successfully saved value: {value}")
        return True

    except Exception as e:
        await session.rollback()
        logger.error(f"Error saving value to the database: {e}")
        return False
