from groq import Groq
from app.config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

class GroqProvider:

    async def generate(self, model, messages):

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        return response.choices[0].message.content
    
    async def generate_stream(self, model, messages):

        try :
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )

            for chunk in stream:
                try:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    if delta is None:
                        continue

                    content = delta.content

                    if content is not None:
                        yield content
                
                except Exception:
                    continue

        except Exception as e:
            yield f"\nERROR: {str(e)}"

    
