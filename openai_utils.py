from openai import OpenAI
client = OpenAI()


def get_transcription(audio_file_path):

    audio_file = open(audio_file_path, "rb")
    transcript = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    return transcript



def get_documentation(transcript_file_path):

    content = open(transcript_file_path, "r").read()
    messages = [
        {
            "role": "user",
            "content": """ Create a documentation in markdown format(ex Readme.MD) from the given content.
             The content contains the entire dialogues by the respective speakers of a transcribed audio. Please use this
             while preparing the documentation, wherever necessary""",
        },
        {"role": "user", "content": content},
    ]

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4-turbo-preview",
    )

    document = chat_completion.choices[0].message.content
    return document