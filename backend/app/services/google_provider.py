import google.generativeai as genai

from app.config.settings import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)


class GoogleProvider:

    def format_messages(self, messages):

        formatted = []

        for msg in messages:

            role = "user"

            if msg["role"] == "assistant":
                role = "model"

            formatted.append({
                "role": role,
                "parts": [msg["content"]]
            })

        return formatted

    async def generate(self, model, messages):

        model_instance = genai.GenerativeModel(model)

        formatted_messages = self.format_messages(messages)

        response = model_instance.generate_content(
            formatted_messages
        )

        return response.text

    async def generate_stream(self, model, messages):

        model_instance = genai.GenerativeModel(model)

        formatted_messages = self.format_messages(messages)

        response = model_instance.generate_content(
            formatted_messages,
            stream=True
        )

        for chunk in response:

            if chunk.text:
                yield chunk.text