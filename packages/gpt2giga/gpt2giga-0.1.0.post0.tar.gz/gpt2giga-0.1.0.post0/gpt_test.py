from pprint import pprint

from openai import OpenAI

client = OpenAI(base_url="http://localhost:8090",
                api_key="0")

#response = client.responses.create(
#    model="gpt-4o",
#    instructions="You are a coding assistant that talks like a pirate.",
#    input="How do I check if a Python object is an instance of a class?",
#)

#print(response.output_text)
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "developer", "content": "Talk like a pirate."},
        {
            "role": "user",
            "content": "Привет как дела?",
        },
    ],
)

print(completion.choices[0].message.content)