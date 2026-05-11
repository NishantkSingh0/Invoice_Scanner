from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def llama4Test(prompt="Hello"):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=6000,
            top_p=1,
            stream=False,
        )

        print(completion.choices[0].message.content)

    except Exception as e:
        print("Error in reading sheet", str(e))
        print("Unable to call llama4")



def llama4(prompt, base64_image, content_type='image/jpeg'):

    try:
        print("llama Called")
        image_data_url = f"data:{content_type};base64,{base64_image}"

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=6000,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        print("parsed successfully")
        return completion.choices[0].message.content

    except Exception as e:
        print("Error in reading sheet", str(e))
        return "unable to parse"