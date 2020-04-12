import base64
import os
from mimetypes import guess_type

from flask import Response

import settings


def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))


def generate_file_path(filename):
    base_filename = filename[:filename.rfind(".")]
    file_extension = filename[filename.rfind(".")+1:]
    ok_filepath = "/".join([
        base_filename[i:i+settings.FILE_TREE_SPLIT_N] for i in range(0, len(base_filename), settings.FILE_TREE_SPLIT_N)
    ])
    return "%s.%s" % (ok_filepath, file_extension)


def file_name(path):
    return os.path.basename(path)


def file_extension(filename):
    return filename[filename.rfind(".") + 1:].lower()


def is_image(filename):
    return file_extension(filename) in settings.IMAGE_EXTENSIONS


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


def full_url(url):
    if is_image(url):
        return "{}/full/{}".format(settings.BASE_URI, file_name(url))
    return url


def is_authorized(request):
    if not settings.UPLOAD_SECRET_CODE:
        return True
    code = request.values.get("code") or request.cookies.get("code")
    return code == settings.UPLOAD_SECRET_CODE


def x_accel_response(filepath):
    """
        Nginx X-Accel Redirect magic.
        That headers will distribute statics files through nginx instead of python.

        Description: http://kovyrin.net/2006/11/01/nginx-x-accel-redirect-php-rails/
    """
    redirect_response = Response(mimetype=guess_type(filepath)[0])
    redirect_response.headers["X-Accel-Redirect"] = filepath
    return redirect_response

