import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Say hello!"}],
    max_tokens=10,
    timeout=30
)
print(response.choices[0].message.content)
