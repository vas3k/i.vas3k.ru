import os.path

BASE_URI = "https://i.vas3k.ru"
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]
IMAGE_QUALITY = 94

CURRENT_DIR = os.path.dirname(__file__)
IMAGES_FILE_PATH = os.path.join(CURRENT_DIR, "images")
FULL_IMAGE_FILE_PATH = os.path.join(IMAGES_FILE_PATH, "max")
TEMPLATES_PATH = os.path.join(CURRENT_DIR, "templates")

PSYCOPG_CONNECTION_STRING = "dbname='ivas3kru' user='vas3k' host='localhost' password='password'"

# to avoid problems due to the large number of files in the directory
# the file tree is made, divided file name by N characters (default = 2)
# for example: abcd.jpg -> ab / cd.jpg, for abcde.jpg -> ab / cd / e.jpg
# DO NOT CHANGE AFTER PRODUCTION RELEASE
FILE_TREE_SPLIT_N = 2

# the maximum length of the wide part of the image saved as the original
ORIGINAL_MAX_IMAGE_LENGTH = 10000  # px

# the length of the wide side of the image returned on request without parameters
COMMON_IMAGE_LENGTH = 1600  # px

