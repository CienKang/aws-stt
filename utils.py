from moviepy.editor import AudioFileClip
from pydub import AudioSegment
from pydub.utils import make_chunks
from dotenv import load_dotenv

import openai_utils
import os

from whisperx.diarize import DiarizationPipeline
from whisperx import load_align_model, align
from whisperx.diarize import assign_word_speakers

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
load_dotenv()

# This function converts video to audio
def convert_video_to_audio(video_file_path, audio_file_path, bitrate='32k'):
    file = AudioFileClip(video_file_path)
    file.write_audiofile(audio_file_path, bitrate=bitrate)
    file.close()



# This function creates chunks from audio of 2 minutes each.
def create_chunks_from_audio(file_name):

    if os.path.exists("chunks"):
        os.system("rm -rf chunks")

    my_audio = AudioSegment.from_file(file=file_name)
    chunk_length_ms = 120000
    chunks = make_chunks(my_audio, chunk_length_ms)

    folder_name = "./chunks"
    os.makedirs(folder_name, exist_ok=True)
    for i, chunk in enumerate(chunks):
        chunk_name = folder_name + "/chunk{0}.wav".format(i)
        chunk.export(chunk_name, format="wav")

    print("Chunks created")

    return len(chunks)


# This function gets the script from the transcription and aligns the speakers
def get_script_from_transcription( audiopath, transcription, transcript_file_path):
    diarization_pipeline = DiarizationPipeline(
        use_auth_token=os.environ.get("HUGGING_FACE_API_KEY"), device="mps"
    )
    diarized = diarization_pipeline(audiopath)
    script_align = []
    for chunk in transcription.segments:
        script_align.append(
            {
                "start": chunk["start"],
                "end": chunk["end"],
                "text": chunk["text"],
            }
        )

    model_a, metadata = load_align_model(language_code="en", device="mps")
    script_aligned = align(script_align, model_a, metadata, audiopath, device="mps")

    # Align Speakers
    result_segments, word_seg = list(
        assign_word_speakers(diarized, script_aligned).values()
    )
    transcribed = []
    for result_segment in result_segments:
        transcribed.append(
            {
                "start": result_segment["start"],
                "end": result_segment["end"],
                "text": result_segment["text"],
                "speaker": (
                    result_segment["speaker"] if "speaker" in result_segment else "."
                ),
            }
        )
    with open(transcript_file_path, "w") as file:
        for start, end, text, speaker in [i.values() for i in transcribed]:
            file.write(f"{speaker} : {text}\n")

    return

    print(os.environ.get("HUGGING_FACE_API_KEY"))


def upload_file_to_s3(file, file_path, s3, S3_BUCKET):
    try:
        s3.upload_fileobj(file, S3_BUCKET, file_path)
    except Exception as e:
        return {"error": e}

    return {"success": True}





# Thread process inside route functions


def thread_process_for_getting_transcription_from_video(video_file_path, audio_file_path, transcript_file_path, documentation_file_path, s3, S3_BUCKET):
    
    upload_file_to_s3(open(video_file_path, "rb"), video_file_path, s3, S3_BUCKET)
    logging.info("Uploaded video file to s3..........")

    # convert video to audio and upload to s3
    convert_video_to_audio(video_file_path, audio_file_path)
    logging.info("Converted video to audio.........")

    upload_file_to_s3(open(audio_file_path, "rb"), audio_file_path, s3, S3_BUCKET)
    logging.info("Uploaded audio file to s3..........")

    #  Check file size of audio file
    audio_file_size = os.path.getsize(audio_file_path)
    logging.info(f"Audio file size: {audio_file_size}")

    if audio_file_size > 25000000:
        final_data = []
        logging.info("Creating chunks from audio file..........")
        num_chunks = create_chunks_from_audio(audio_file_path)
        for i in range(num_chunks):
            chunk_name = f"chunks/chunk{i}.wav"
            logging.info(f"Processing chunk {i} to whisper ai..........")
            transcription = openai_utils.get_transcription(chunk_name)
            final_data.append(transcription)

        logging.info("Diarization started..........")
        get_script_from_transcription( audio_file_path, transcription, transcript_file_path)
        logging.info("Diarization completed..........")


        logging.info("Creating documentation..........")
        document_data = openai_utils.get_documentation(transcript_file_path)
        with open(documentation_file_path, "w") as f:
            f.write(document_data)
        logging.info("Documentation created..........")
    
    else:
        logging.info("Processing audio file to whisper ai..........")
        transcription = openai_utils.get_transcription(audio_file_path)

        logging.info("Diarization started..........")
        get_script_from_transcription( audio_file_path, transcription, transcript_file_path)
        logging.info("Diarization completed..........")

        logging.info("Creating documentation..........")
        document_data = openai_utils.get_documentation(transcript_file_path)
        with open(documentation_file_path, "w") as f:
            f.write(document_data)
        logging.info("Documentation created..........")


    logging.info("Uploading transcript to s3..........")
    upload_file_to_s3(open(transcript_file_path, "rb"), transcript_file_path, s3, S3_BUCKET)
    logging.info("Uploaded documentation file to s3..........")
    upload_file_to_s3(open(documentation_file_path, "rb"), documentation_file_path, s3, S3_BUCKET)

    os.remove(video_file_path)
    os.remove(audio_file_path)
    os.remove(transcript_file_path)
    os.remove(documentation_file_path)



def thread_process_for_getting_transcription_from_audio(audio_file_path, transcript_file_path, s3, S3_BUCKET):
    
    upload_file_to_s3(open(audio_file_path, "rb"), audio_file_path, s3, S3_BUCKET)
    logging.info("Uploaded audio file to s3..........")

    logging.info("Starting Whisper Model..........")
    # get transcription and upload to s3
    transcript = openai_utils.get_transcription(audio_file_path)
    with open(transcript_file_path, "w") as f:
        f.write(transcript.text)

    logging.info("Transcription created successful..........")
    upload_file_to_s3(open(transcript_file_path, "rb"), transcript_file_path, s3, S3_BUCKET)
    logging.info("Uploaded transcript file to s3..........")

    os.remove(audio_file_path)
    os.remove(transcript_file_path)


    
def thread_process_for_getting_documentation(transcript_file_path, documentation_file_path, transcript, s3, S3_BUCKET):
    
    logging.info("Creating documentation..........")
    content = openai_utils.get_documentation(transcript)

    logging.info("Documentation created..........")

    with open(documentation_file_path, "w") as f:
        f.write(content.choices[0].message.content)


    upload_file_to_s3(open(documentation_file_path, "rb"), documentation_file_path, s3, S3_BUCKET)
    logging.info("Uploaded documentation file to s3..........")

    os.remove(documentation_file_path)
    os.remove(transcript_file_path)
