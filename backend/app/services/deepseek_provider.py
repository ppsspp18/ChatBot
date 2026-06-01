from openai import OpenAI
from app.config.settings import DEEPSEEK_API_KEY

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


class DeepSeekProvider:

    async def generate(self, model, messages):

        messages = [
            {
                "role": "system",
                "content": "Do the conversation will be in English."
            }
        ] + messages


        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        return response.choices[0].message.content

    async def generate_stream(self, model, messages):

        messages = [
            {
                "role": "system",
                "content": "The conversation will be in English."
            }
        ] + messages

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True
        )

        for chunk in stream:

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta.content

            if delta:
                yield delta