import os

import ffmpeg

import settings
from helpers import generate_file_path


def save_and_transcode_video(data, extension, file_code):
    save_file_path = os.path.join(
        settings.VIDEOS_FILE_PATH,
        generate_file_path("{}.{}".format(file_code, extension))
    )

    save_dir = save_file_path[:save_file_path.rfind("/") + 1]
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, mode=0o777)

    with open(save_file_path, "wb") as f:
        f.write(data)

    long_file_name = "{}.{}".format(file_code, settings.VIDEO_OUTPUT_EXTENSION)
    transcoded_file_path = os.path.join(
        settings.VIDEOS_FILE_PATH,
        generate_file_path(long_file_name)
    )

    ffmpeg\
        .input(save_file_path)\
        .filter("scale", height=settings.VIDEO_OUTPUT_HEIGHT, width="trunc(oh*a/2)*2")\
        .output(transcoded_file_path, **settings.VIDEO_OUTPUT_SETTINGS)\
        .overwrite_output()\
        .run(cmd=settings.FFMPEG_PATH)

    if extension != settings.VIDEO_OUTPUT_EXTENSION:
        os.remove(save_file_path)

    return long_file_name, transcoded_file_path
