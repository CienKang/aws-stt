import json
import cv2
import os
import openai_utils
import datetime

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def generate_timestamps(start_time, end_time):
    if "." in start_time:
        start = datetime.datetime.strptime(start_time, "%H:%M:%S.%f")
    else:
        start = datetime.datetime.strptime(start_time, "%H:%M:%S")

    if "." in end_time:
        end = datetime.datetime.strptime(end_time, "%H:%M:%S.%f")
    else:
        end = datetime.datetime.strptime(end_time, "%H:%M:%S")
    timestamps_as_objects = []
    timestamps_as_strings = []
    current = start

    while current <= end:

        hours = current.hour
        minutes = current.minute
        seconds = current.second + current.microsecond / 1000000

        timestamps_as_objects.append(
            {
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
            }
        )
        timestamps_as_strings.append(f"{hours}:{minutes}:{int(seconds)}")
        current += datetime.timedelta(seconds=15)

    return timestamps_as_objects, timestamps_as_strings


def split_time_intervals(time_intervals):
    split_timestamps_as_objects = []
    split_timestamps_as_strings = []
    for interval in time_intervals:
        start_time = interval["start"]
        end_time = interval["end"]
        timestamps_as_objects, timestamps_as_strings = generate_timestamps(
            start_time, end_time
        )
        split_timestamps_as_objects.extend(timestamps_as_objects)
        split_timestamps_as_strings.extend(timestamps_as_strings)

    return split_timestamps_as_objects, split_timestamps_as_strings



def prepare_screenshots(documentation_file_path):

    timestamps_as_strings = openai_utils.get_timestamps(documentation_file_path)

    ranges_json = json.loads(timestamps_as_strings)
    ranges_data = ranges_json[list(ranges_json.keys())[0]]
    split_timestamps_as_objects, split_timestamps_as_strings = split_time_intervals(
        ranges_data
    )

    return (split_timestamps_as_objects, split_timestamps_as_strings)




def capture_frame(timestamps, videopath, video_name):
    video = cv2.VideoCapture(videopath)
    fps = video.get(cv2.CAP_PROP_FPS)

    for stamp in timestamps:
        logging.info(f"Capturing frame for {stamp}")
        hours = stamp["hours"]
        minutes = stamp["minutes"]
        seconds = int(stamp["seconds"])
        milli_timestamp = (hours * 3600 + minutes * 60 + seconds) * 1000
        frame_id = int(fps * (milli_timestamp / 1000))
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = video.read()
        os.makedirs(f"screenshots/{video_name}", exist_ok=True)

        cv2.imwrite(f"screenshots/{video_name}/{hours}:{minutes}:{seconds}.png", frame)

    return None

