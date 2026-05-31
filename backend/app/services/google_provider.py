import google.generativeai as genai

from app.config.settings import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

class GoogleProvider:

    async def generate(self, model, prompt):

        model_instance = genai.GenerativeModel(model)

        response = model_instance.generate_content(
            prompt
        )

        return response.text
