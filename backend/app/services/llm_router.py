from app.services.groq_provider import GroqProvider
from app.services.google_provider import GoogleProvider

class LLMRouter:

    def __init__(self):

        self.providers = {
            "groq": GroqProvider(),
            "google": GoogleProvider()
        }

    async def generate(self, provider, model, prompt):

        provider_instance = self.providers.get(provider)

        if not provider_instance:
            raise Exception("Provider not supported")

        return await provider_instance.generate(
            model=model,
            prompt=prompt
        )

router = LLMRouter()