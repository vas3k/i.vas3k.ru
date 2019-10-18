import os.path

DEBUG = True
UPLOAD_SECRET_CODE = None
BASE_URI = "https://i.vas3k.ru"
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]
VIDEO_EXTENSIONS = ["mp4", "mov", "gif"]
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

CURRENT_DIR = os.path.dirname(__file__)
TEMPLATES_PATH = os.path.join(CURRENT_DIR, "templates")

PSYCOPG_CONNECTION_STRING = "dbname='ivas3kru' user='postgres' host='localhost' password=''"

# to avoid problems due to the large number of files in the directory
# the file tree is made, divided file name by N characters (default = 2)
# for example: abcd.jpg -> ab / cd.jpg, for abcde.jpg -> ab / cd / e.jpg
FILE_TREE_SPLIT_N = 2  # DO NOT CHANGE IT AFTER RELEASE

# Images

IMAGE_QUALITY = 93
IMAGES_FILE_PATH = os.path.join(CURRENT_DIR, "images")
FULL_IMAGE_FILE_PATH = os.path.join(IMAGES_FILE_PATH, "max")
ORIGINAL_IMAGE_MAX_LENGTH = 10000  # px
DEFAULT_IMAGE_LENGTH = 1600  # px

# Videos

FFMPEG_PATH = "ffmpeg"
VIDEOS_FILE_PATH = os.path.join(CURRENT_DIR, "videos")
ORIGINAL_VIDEO_MAX_SIZE = 300 * 1000 * 1000  # 300 Mb
VIDEO_OUTPUT_HEIGHT = 432
VIDEO_OUTPUT_EXTENSION = "mp4"
VIDEO_OUTPUT_SETTINGS = {
    "crf": 25,
    "preset": "slow",
    "profile:v": "baseline",
    "codec:v": "libx264",
    "maxrate": "500k",
    "bufsize": "1000k",
    "codec:a": "libfdk_aac",
    "b:a": "128k"
}

try:
    from local_settings import *
except ImportError:
    pass
