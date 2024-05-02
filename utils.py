from moviepy.editor import AudioFileClip
import openai_utils
import postgres.files_utils as files_utils
import os
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def convert_video_to_audio(video_file_path, audio_file_path, bitrate='32k'):
    file = AudioFileClip(video_file_path)
    file.write_audiofile(audio_file_path, bitrate=bitrate)
    file.close()


def upload_file_to_s3(file, file_path, s3, S3_BUCKET):
    try:
        s3.upload_fileobj(file, S3_BUCKET, file_path)
    except Exception as e:
        return {"error": e}

    return {"success": True}


def delete_file_from_s3(file_path, s3, S3_BUCKET):
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=file_path)
    except Exception as e:
        return {"error": e}

    return {
        "success": True,
        "message": "File deleted successfully."
    }


def thread_process_for_getting_transcription_from_video(video_file_path, audio_file_path, transcript_file_path, documentation_file_path, s3, S3_BUCKET):
    
    upload_file_to_s3(open(video_file_path, "rb"), video_file_path, s3, S3_BUCKET)
    logging.info("Uploaded video file to s3..........")
    files_utils.update_file_status(video_file_path.split("/")[1], True)

    # convert video to audio and upload to s3
    convert_video_to_audio(video_file_path, audio_file_path)
    logging.info("Converted video to audio.........")

    upload_file_to_s3(open(audio_file_path, "rb"), audio_file_path, s3, S3_BUCKET)
    logging.info("Uploaded audio file to s3..........")
    files_utils.update_file_status(audio_file_path.split("/")[1], True)



    logging.info("Starting Whisper Model..........")
    # get transcription and upload to s3
    transcript = openai_utils.get_transcription(audio_file_path)
    with open(transcript_file_path, "w") as f:
        f.write(transcript.text)
    logging.info("Transcription created successful..........")
    upload_file_to_s3(open(transcript_file_path, "rb"), transcript_file_path, s3, S3_BUCKET)
    logging.info("Uploaded transcript file to s3..........")
    files_utils.update_file_status(transcript_file_path.split("/")[1], True)


    # Create documentation and upload to s3
    logging.info("Creating documentation..........")
    content = openai_utils.get_documentation(transcript.text)
    logging.info("Documentation created..........")
    with open(documentation_file_path, "w") as f:
        f.write(content.choices[0].message.content)
    upload_file_to_s3(open(documentation_file_path, "rb"), documentation_file_path, s3, S3_BUCKET)
    logging.info("Uploaded documentation file to s3..........")
    files_utils.update_file_status(documentation_file_path.split("/")[1], True)

    os.remove(video_file_path)
    os.remove(audio_file_path)
    os.remove(transcript_file_path)
    os.remove(documentation_file_path)