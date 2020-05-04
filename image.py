import io
import logging
import os

from PIL import ExifTags, Image

import settings
from helpers import generate_file_path

logger = logging.getLogger(__name__)


def save_full_image(data, extension, file_code, convert_to=None, quality=settings.IMAGE_QUALITY):
    long_file_name = "{}.{}".format(file_code, extension)
    save_file_path = os.path.join(
        settings.FULL_IMAGE_FILE_PATH,
        generate_file_path(long_file_name)
    )

    save_dir = save_file_path[:save_file_path.rfind("/") + 1]
    if not os.path.exists(save_dir):
        os.makedirs(save_dir, mode=0o777)

    file = io.BytesIO(data)
    image = Image.open(file)

    image_width = float(image.size[0])
    image_height = float(image.size[1])
    orig_save_size = get_fit_image_size(image_width, image_height, settings.ORIGINAL_IMAGE_MAX_LENGTH)
    image.thumbnail(orig_save_size, Image.ANTIALIAS)

    if convert_to:
        convert_to = convert_to.strip().lower()
        if convert_to not in settings.IMAGE_EXTENSIONS:
            logger.error("Unknown extension to convert: {}".format(convert_to))
        else:
            if image.mode == "RGBA" and convert_to == "jpg":
                # need to convert RGBA -> RGB with white background before saving
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])  # 3 is the alpha channel
                image = rgb_image

            save_file_path = os.path.splitext(save_file_path)[0] + "." + convert_to
            long_file_name = os.path.splitext(long_file_name)[0] + "." + convert_to

    try:
        image = auto_rotate_by_exif(image)
    except (IOError, KeyError, AttributeError) as ex:
        logger.error("Auto-rotation error: {}".format(ex))

    image.save(save_file_path, quality=quality)

    return long_file_name, save_file_path


def get_fit_image_size(image_width, image_height, max_length):
    if image_width > image_height:  # landscape
        new_width = max_length
        new_height = new_width / image_width * image_height
        return int(new_width), int(new_height)
    elif image_width < image_height:  # portrait
        new_height = max_length
        new_width = new_height / image_height * image_width
        return int(new_width), int(new_height)
    else:  # square
        return int(max_length), int(max_length)


ORIENTATION_NORM = 1
ORIENTATION_UPSIDE_DOWN = 3
ORIENTATION_RIGHT = 6
ORIENTATION_LEFT = 8


def auto_rotate_by_exif(image):
    orientation = None
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break

    if hasattr(image, '_getexif'):  # only present in JPEGs
        exif = image._getexif()        # returns None if no EXIF data
        if exif is not None:
            exif = dict(exif.items())
            orientation = exif[orientation]

            if orientation == ORIENTATION_UPSIDE_DOWN:
                return image.transpose(Image.ROTATE_180)
            elif orientation == ORIENTATION_RIGHT:
                return image.transpose(Image.ROTATE_270)
            elif orientation == ORIENTATION_LEFT:
                return image.transpose(Image.ROTATE_90)

    return image
