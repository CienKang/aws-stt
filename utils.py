from moviepy.editor import AudioFileClip
import openai_utils
import frame_capture
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



def thread_process_for_getting_transcription_from_video(video_file_path, audio_file_path, transcript_file_path, documentation_file_path, s3, S3_BUCKET, S3_IMAGE_BUCKET):
    
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
        for segment in transcript.segments:
            start = segment['start']
            end = segment['end']
            text = segment['text']
            start_time_srt = "{:02}:{:02}:{:06.3f}".format(
                int(start // 3600), int((start % 3600) // 60), start % 60
            )
            end_time_srt = "{:02}:{:02}:{:06.3f}".format(
                int(end // 3600), int((end % 3600) // 60), end % 60
            )
            f.write(f"{start_time_srt} --> {end_time_srt}\n")
            f.write(f"{text}\n\n")

    logging.info("Transcription created successful..........")
    upload_file_to_s3(open(transcript_file_path, "rb"), transcript_file_path, s3, S3_BUCKET)
    logging.info("Uploaded transcript file to s3..........")
    files_utils.update_file_status(transcript_file_path.split("/")[1], True)


    # Create documentation
    logging.info("Creating documentation..........")
    content = openai_utils.get_documentation(transcript_file_path)
    logging.info("Documentation created..........")
    with open(documentation_file_path, "w") as f:
        f.write(content)

    # Getting timestamp from documentation
    logging.info("Getting timestamps..........")
    split_timestamps_as_objects, split_timestamps_as_strings = frame_capture.prepare_screenshots(documentation_file_path)
    logging.info("Timestamps created..........")

    # Capture frames
    logging.info("Capturing frames..........")
    frame_capture.capture_frame(split_timestamps_as_objects, video_file_path, video_name=video_file_path.split('/')[-1])
    logging.info("Frames captured..........")
    

    screenshots_file_path = f"screenshots/{video_file_path.split('/')[-1]}"


    # for each screenshot upload to s3
    s3_screenshot_urls = []
    for screenshot in os.listdir(screenshots_file_path):
        upload_file_to_s3(open(screenshots_file_path + "/" + screenshot, "rb"), screenshots_file_path + "/" + screenshot, s3, S3_IMAGE_BUCKET)
        logging.info(f"Uploaded screenshot {screenshot} to s3..........")
        s3_screenshot_urls.append(f"https://{S3_IMAGE_BUCKET}.s3.amazonaws.com/{screenshots_file_path}/{screenshot}")
    
    new_content = openai_utils.modify_md_file(s3_screenshot_urls, documentation_file_path, video_file_path.split('/')[-1], S3_IMAGE_BUCKET)

    with open(documentation_file_path, "w") as f:
        f.write(new_content)

    upload_file_to_s3(open(documentation_file_path, "rb"), documentation_file_path, s3, S3_BUCKET)
    logging.info("Uploaded documentation file to s3..........")
    files_utils.update_file_status(documentation_file_path.split("/")[1], True)

    os.remove(video_file_path)
    os.remove(audio_file_path)
    os.remove(transcript_file_path)
    os.remove(documentation_file_path)
    for screenshot in os.listdir(screenshots_file_path):
        os.remove(screenshots_file_path + "/" + screenshot)
    
    