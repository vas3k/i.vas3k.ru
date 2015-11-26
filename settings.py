import os.path

BASE_URI = "http://i.vas3k.ru"
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]

CURRENT_DIR = os.path.dirname(__file__)
IMAGES_FILE_PATH = os.path.join(CURRENT_DIR, "images")
FULL_IMAGE_FILE_PATH = os.path.join(IMAGES_FILE_PATH, "max")

# папка с html-шаблонами
TEMPLATES_PATH = os.path.join(CURRENT_DIR, "templates")

# сюда в txt-файлы складываются json-ответы от твиттера и пока нигде не используются
INFO_FILE_PATH = os.path.join(CURRENT_DIR, "info")

# текстовый файл, хранящий количество загруженных картинок (id'шник)
ID_FILE_PATH = os.path.join(INFO_FILE_PATH, "last_image_id.txt")

# чтобы избежать проблем из-за большого количества файлов в директории
# делается дерево, разбиением по N символов (default=2)
# например для файла abcd.jpg -> ab/cd.jpg, для abcde.jpg -> ab/cd/e.jpg
# без необходимости лучше не менять, на других значениях я не тестил
FILE_TREE_SPLIT_N = 2

# максимальная длина широкой части изображения, сохраняемого как оригинал
ORIGINAL_MAX_IMAGE_LENGTH = 2500

# длина широкой стороны изображения, возвращаемого по запросу без параметров
COMMON_IMAGE_LENGTH = 1200

# длина широкой стороны изображения, выдаваемого в списке на главной
LIST_IMAGE_LENGTH = 480

# количество изображений выдаваемых на страницу в списке на главной
IMAGES_PER_PAGE = 200

# качество изображений
IMAGE_QUALITY = 95

# БД
PSYCOPG_CONNECTION_STRING = "dbname='ivas3kru' user='vas3k' host='localhost' password='password'"
