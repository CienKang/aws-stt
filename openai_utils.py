from openai import OpenAI
client = OpenAI()


def get_transcription(audio_file_path):

    file = open(audio_file_path, "rb")
    transcript = client.audio.transcriptions.create(
    model="whisper-1", 
    file=file, 
    response_format="verbose_json",
    language="en"
    )

    return transcript



def get_documentation(transcript):
    content = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": '''You are a helpful assistant. You have to create a documentations for the audio file. 
             Write steps on what to do as said in the audio file. Make it look professional. 
             Dont put anything not related to the technical documentation.
             Also dont add anything form your own. Just keep what was said in the video.
              Make it look like a readme.md file.
             It should strictly contain readme.md file format. No ```mardown something like that'''},
            {"role": "user", "content": transcript}
        ]
    )

    return content