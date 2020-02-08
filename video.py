import os

import ffmpeg

import settings
from helpers import generate_file_path


def save_and_transcode_video(data, extension, file_code):
    temp_file_path = os.path.join(
        settings.VIDEOS_FILE_PATH,
        generate_file_path("{}.{}".format(file_code, extension))
    ) + "_tmp"

    save_dir = temp_file_path[:temp_file_path.rfind("/") + 1]
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, mode=0o777)

    with open(temp_file_path, "wb") as f:
        f.write(data)

    long_file_name = "{}.{}".format(file_code, settings.VIDEO_OUTPUT_EXTENSION)
    save_file_path = os.path.join(
        settings.VIDEOS_FILE_PATH,
        generate_file_path(long_file_name)
    )

    ffmpeg\
        .input(temp_file_path)\
        .filter("scale", height=settings.VIDEO_OUTPUT_HEIGHT, width="trunc(oh*a/2)*2")\
        .output(save_file_path, **settings.VIDEO_OUTPUT_SETTINGS)\
        .run(cmd=settings.FFMPEG_PATH)

    os.remove(temp_file_path)

    return long_file_name, save_file_path
