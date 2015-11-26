import base64
from PIL import Image, ExifTags
from settings import FILE_TREE_SPLIT_N

__all__ = ["base36_encode", "get_fit_image_size", "apply_rotation_by_exif", "file_path", "convert_param_to_data"]


def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))


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


def apply_rotation_by_exif(image):
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


def file_path(filename):
    base_filename = filename[:filename.rfind(".")]
    file_extension = filename[filename.rfind(".")+1:]
    ok_filepath = "/".join([base_filename[i:i+FILE_TREE_SPLIT_N] for i in range(0, len(base_filename), FILE_TREE_SPLIT_N)])
    return "%s.%s" % (ok_filepath, file_extension)


def convert_param_to_data(data):
    try:
        prefixes = {
            "data:image/png;base64": "png",
            "data:image/jpeg;base64": "jpg"
        }
        for prefix, extension in prefixes.items():
            if data.startswith(prefix):
                return base64.b64decode(data[len(prefix)+1:]), extension
        else:
            raise None
    except TypeError:
        return None
