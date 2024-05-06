from openai import OpenAI
client = OpenAI()


def get_transcription(audio_path):
    audio_file = open(audio_path, "rb")
    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )
    return transcription




def get_documentation(transcript_file_path):
    content = open(transcript_file_path, "r").read()
    messages = [
        {
            "role": "user",
            "content": f""" 
            Create a detailed documentation in markdown format(ex Readme.MD) from the given content.
             The content contains the dialogues with the timestamps by the respective speakers of a transcribed video .
             Use this information to create the documentation and  include the the timestamps in the documentation headings.
             No markings like ```markdown must be included in the output.
             
            """,
        },
        {"role": "user", "content": content},
    ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4-turbo-preview",
    )

    document = chat_completion.choices[0].message.content
    return document

def get_timestamps(script_file_path):
    content = open(script_file_path, "r").read()
    messages = [
        {
            "role": "user",
            "content": f"""                              
                       Extract all distinct  ranges of timestamps from the markdown text given below and sort them in ascending order .Then return it as a json. 
                       Each element of the json object must look as given below.
                       (
                           'start':'start value of the range.',
                           'end': 'ending value of the range.'
                           
                       )
                       markdown content:{content}
               
            """,
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4-0125-preview",
        response_format={"type": "json_object"},
    )
    timestamps = chat_completion.choices[0].message.content

    return timestamps

def modify_md_file(screenshot_timestamps, md_file_path, video_name, S3_IMAGE_BUCKET):
    content = open(md_file_path, "r").read()
    messages = [
        {
            "role": "user",
            "content": f"""                              
                       
                       You have a Markdown file with content and timestamp, along with a list of additional timestamps. 
                       Each element in timestamp list in the list corresponds to an  url  of image file located at `https://{S3_IMAGE_BUCKET}.s3.amazonaws.com/screenshots/{video_name}/timestamp_value.png`. 
                       The timestamps in the Markdown file and in the list are in hh:mm:ss format.
                       
                       Your goal is to add these images to the Markdown file content just below where the corresponding timestamp is located, but only if the timestamp falls within the time range specified by the timestamps in the Markdown file 
                       and without modifying the original file content or the list values.
                       
                       Original File content in markdown format (Do Not Modify):
                       {content}
                       
                       List of Timestamps :
                       {screenshot_timestamps}
                       
                       Your task is to process this data and include the images specified by list in the Markdown file content just below where the corresponding timestamp from list is located in original file content only if it falls within the time range specified by the timestamps in the original file content.
                       Ensure that the timestamps are compared correctly using the following criteria:

                        1. If the timestamp in the list is greater than or equal to the start timestamp and less than the end timestamp in original file content, include the image.
                        2. If the timestamp in list is equal to the end timestamp in original file content, include the image. 
                       
                       Provide the modified Markdown file directly as the output without altering the original content and the timestamp values in the list.
                       No markings like ```markdown must be included in the output.
                       
                       
                       
               
            """,
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4-0125-preview",
    )
    md_file_with_screenshots = chat_completion.choices[0].message.content

    return md_file_with_screenshots