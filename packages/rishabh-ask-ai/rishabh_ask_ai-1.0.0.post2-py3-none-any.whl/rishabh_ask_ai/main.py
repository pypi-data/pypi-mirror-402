from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq()
def ask(input):
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": input}
        ],
        temperature=0.7,
        max_completion_tokens=1000,
        top_p=1,
    )

    return completion.choices[0].message.content