import io
import sys
import json
import logging
from mimetypes import guess_type

from PIL import Image
from flask import Flask, redirect, request, render_template, Response
import psycopg2
import psycopg2.extras

from helpers import *
from settings import *

app = Flask(__name__)
app.debug = True

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def x_accel_response(filepath):
    # nginx x-accel internal redirect 
    # magic headers, that distributes statics files through nginx instead of python
    # here is a description http://kovyrin.net/2006/11/01/nginx-x-accel-redirect-php-rails/
    redirect_response = Response(mimetype=guess_type(filepath)[0])
    redirect_response.headers["X-Accel-Redirect"] = filepath
    return redirect_response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload/", methods=["POST"])
def upload():
    files = request.files.getlist("media") or request.files.getlist("image")
    data = request.form.get("media") or request.form.get("image")

    images = []
    if files:
        for image_file in files:
            image_extension = image_file.filename[image_file.filename.rfind(".") + 1:].lower()
            if image_extension not in ALLOWED_EXTENSIONS:
                return "{} is not allowed".format(image_extension)
            data = image_file.read()
            images.append((data, image_extension))
    elif data:
        data, image_extension = convert_param_to_data(data)
        if image_extension not in ALLOWED_EXTENSIONS:
            return "{} is not allowed".format(image_extension)
        images.append((data, image_extension))

    db = psycopg2.connect(PSYCOPG_CONNECTION_STRING)
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    uploaded_image_names = []

    for image in images:
        data, image_extension = image

        cursor.execute("insert into images values (default, null, now()) returning id")
        file_id = cursor.fetchone()[0]

        image_code = base36_encode(file_id)
        image_path = os.path.join(FULL_IMAGE_FILE_PATH, file_path("{}.{}".format(image_code, image_extension)))

        image_dir = image_path[:image_path.rfind("/") + 1]
        if not os.path.exists(image_dir):
            os.makedirs(image_dir, mode=0o777)

        try:
            image_file = io.BytesIO(data)
            image = Image.open(image_file)
        except IOError as ex:
            cursor.execute("delete from images where id = %s", [file_id])
            db.commit()
            cursor.close()
            return "Image upload error (maybe not image?): {}".format(ex)

        image_width = float(image.size[0])
        image_height = float(image.size[1])
        orig_save_size = get_fit_image_size(image_width, image_height, ORIGINAL_MAX_IMAGE_LENGTH)
        image.thumbnail(orig_save_size, Image.ANTIALIAS)

        try:
            image = apply_rotation_by_exif(image)
        except (IOError, KeyError, AttributeError) as ex:
            log.error("Auto-rotation error: {}".format(ex))

        image.save(image_path, quality=IMAGE_QUALITY)
        image_name = "{}.{}".format(image_code, image_extension)
        cursor.execute("update images set image = %s, file = %s where id = %s", [image_name, image_path, file_id])
        db.commit()

        uploaded_image_names.append(image_name)

    cursor.close()
    db.close()

    if request.form.get("nojson"):
        return redirect("{}/meta/{}".format(BASE_URI, "+".join(uploaded_image_names)))
    else:
        return json.dumps({
            "uploaded": [
                "{}/{}".format(BASE_URI, image_name) for image_name in uploaded_image_names
            ]
        })


@app.route("/<filename>", methods=["GET"])
def common_image(filename):
    return fit_image(COMMON_IMAGE_LENGTH, filename)


@app.route("/full/<filename>", methods=["GET"])
def full_image(filename):
    return x_accel_response("/images/max/{}".format(file_path(filename)))


@app.route("/meta/<filenames>", methods=["GET"])
def meta_image(filenames):
    filenames = filenames.split("+")
    return render_template(
        "meta.html",
        images=[
            (
                "{}/{}".format(BASE_URI, filename),
                "{}/full/{}".format(BASE_URI, filename)
            ) for filename in filenames
        ]
    )


@app.route("/<int(min=50,max=2000):max_length>/<filename>", methods=["GET"])
def fit_image(max_length, filename):
    ok_filepath = file_path(filename)
    filepath = os.path.join(IMAGES_FILE_PATH, "resize/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(FULL_IMAGE_FILE_PATH, ok_filepath))
        except IOError:
            return "Not found", 404

        image_dir = filepath[:filepath.rfind("/") + 1]
        if not os.path.exists(image_dir):
            os.makedirs(image_dir, mode=0o777)

        image_width = float(image.size[0])
        image_height = float(image.size[1])
        if image_width > max_length or image_height > max_length:
            new_width, new_height = get_fit_image_size(image_width, image_height, max_length)
            image.thumbnail((new_width, new_height), Image.ANTIALIAS)
        image.save(filepath, quality=IMAGE_QUALITY)

    return x_accel_response("/images/resize/{}/{}".format(max_length, ok_filepath))


@app.route("/square/<int(min=50,max=2000):max_length>/<filename>", methods=["GET"])
def square_image(max_length, filename):
    ok_filepath = file_path(filename)
    filepath = os.path.join(IMAGES_FILE_PATH, "square/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(FULL_IMAGE_FILE_PATH, ok_filepath))
        except IOError:
            return "Not found", 404

        image_dir = filepath[:filepath.rfind("/") + 1]
        if not os.path.exists(image_dir):
            os.makedirs(image_dir, mode=0o777)

        image_width = float(image.size[0])
        image_height = float(image.size[1])
        image_square = int(min(image_width, image_height))
        crop_coordinates_x = int(image_width / 2 - image_square / 2)
        crop_coordinates_y = int(image_height / 2 - image_square / 2)
        image = image.crop((crop_coordinates_x, crop_coordinates_y, crop_coordinates_x + image_square,
                            crop_coordinates_y + image_square))
        image.thumbnail((max_length, max_length), Image.ANTIALIAS)
        image.save(filepath, quality=IMAGE_QUALITY)

    return x_accel_response("/images/square/{}/{}".format(max_length, ok_filepath))


@app.route("/width/<int(min=50,max=2000):max_length>/<filename>", methods=["GET"])
def width_image(max_length, filename):
    ok_filepath = file_path(filename)
    filepath = os.path.join(IMAGES_FILE_PATH, "width/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(FULL_IMAGE_FILE_PATH, ok_filepath))
        except IOError:
            return "Not found", 404

        image_dir = filepath[:filepath.rfind("/") + 1]
        if not os.path.exists(image_dir):
            os.makedirs(image_dir, mode=0o777)

        image_width = float(image.size[0])
        image_height = float(image.size[1])
        new_width = int(max_length)
        new_height = int(new_width / image_width * image_height)
        image.thumbnail((new_width, new_height), Image.ANTIALIAS)
        image.save(filepath, quality=IMAGE_QUALITY)

    return x_accel_response("/images/width/{}/{}".format(max_length, ok_filepath))


if __name__ == '__main__':
    app.run()
