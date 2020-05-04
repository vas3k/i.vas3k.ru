import os
import sys
import json
import logging

from PIL import Image
from flask import Flask, redirect, request, render_template, make_response, abort
import psycopg2
import psycopg2.extras

import settings
from helpers import generate_file_path, convert_param_to_data, base36_encode, x_accel_response, file_extension, \
    is_image, full_url, is_authorized
from image import get_fit_image_size, save_full_image
from video import save_and_transcode_video

app = Flask(__name__)
app.debug = settings.DEBUG
app.jinja_env.globals.update(is_image=is_image, full_url=full_url)

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@app.route("/")
def index():
    response = make_response(
        render_template("index.html", has_access=is_authorized(request))
    )

    code = request.args.get("code") or request.cookies.get("code")
    if code:
        response.set_cookie("code", code)

    return response


@app.route("/upload/", methods=["POST"])
def upload():
    if not is_authorized(request):
        abort(401, "Not authorized")

    files = request.files.getlist("media") or request.files.getlist("image")
    data = request.form.get("media") or request.form.get("image")
    convert_to = request.values.get("convert_to")
    quality = int(request.values.get("quality") or settings.IMAGE_QUALITY)

    images = []
    if files:
        for file in files:
            extension = file_extension(file.filename)
            if extension not in settings.ALLOWED_EXTENSIONS:
                return "{}'s are not allowed".format(extension)
            data = file.read()
            images.append((data, extension))
    elif data:
        data, extension = convert_param_to_data(data)
        if extension not in settings.ALLOWED_EXTENSIONS:
            return "{}'s are not allowed".format(extension)
        images.append((data, extension))

    db = psycopg2.connect(settings.PSYCOPG_CONNECTION_STRING)
    cursor = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    uploaded_file_names = []

    for image in images:
        data, extension = image
        cursor.execute("insert into images values (default, null, now()) returning id")
        file_id = cursor.fetchone()[0]
        file_code = base36_encode(file_id)

        if extension in settings.IMAGE_EXTENSIONS:
            try:
                public_file_name, saved_file_path = save_full_image(
                    data=data,
                    extension=extension,
                    file_code=file_code,
                    convert_to=convert_to,
                    quality=quality,
                )
            except IOError as ex:
                cursor.execute("delete from images where id = %s", [file_id])
                db.commit()
                cursor.close()
                return "Image upload error: {}".format(ex)
        elif extension in settings.VIDEO_EXTENSIONS:
            try:
                public_file_name, saved_file_path = save_and_transcode_video(data, extension, file_code)
            except IOError as ex:
                cursor.execute("delete from images where id = %s", [file_id])
                db.commit()
                cursor.close()
                return "Video upload error: {}".format(ex)
        else:
            return "Unknown file extension: {}".format(extension)

        cursor.execute("update images set image = %s, file = %s where id = %s", [
            public_file_name, saved_file_path, file_id
        ])
        db.commit()

        uploaded_file_names.append(public_file_name)

    cursor.close()
    db.close()

    if request.form.get("nojson"):
        return redirect("{}/meta/{}".format(settings.BASE_URI, "+".join(uploaded_file_names)))
    else:
        return json.dumps({
            "uploaded": [
                "{}/{}".format(settings.BASE_URI, image_name) for image_name in uploaded_file_names
            ]
        })


@app.route("/meta/<filenames>", methods=["GET"])
def meta(filenames):
    filenames = filenames.split("+")
    return render_template(
        "meta.html",
        urls=[
            "{}/{}".format(settings.BASE_URI, filename) for filename in filenames
        ]
    )


@app.route("/<filename>", methods=["GET"])
def normal_size_media(filename):
    if is_image(filename):
        return length_fit_media(settings.DEFAULT_IMAGE_LENGTH, filename)
    return full_media(filename)


@app.route("/full/<filename>", methods=["GET"])
def full_media(filename):
    if is_image(filename):
        return x_accel_response("/images/max/{}".format(generate_file_path(filename)))
    return x_accel_response("/videos/{}".format(generate_file_path(filename)))


@app.route("/<int(min=100,max=2500):max_length>/<filename>", methods=["GET"])
def length_fit_media(max_length, filename):
    if not is_image(filename):
        return full_media(filename)

    ok_filepath = generate_file_path(filename)
    filepath = os.path.join(settings.IMAGES_FILE_PATH, "resize/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(settings.FULL_IMAGE_FILE_PATH, ok_filepath))
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
        image.save(filepath, quality=settings.IMAGE_QUALITY)

    return x_accel_response("/images/resize/{}/{}".format(max_length, ok_filepath))


@app.route("/square/<int(min=50,max=2000):max_length>/<filename>", methods=["GET"])
def square_fit_media(max_length, filename):
    if not is_image(filename):
        return full_media(filename)

    ok_filepath = generate_file_path(filename)
    filepath = os.path.join(settings.IMAGES_FILE_PATH, "square/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(settings.FULL_IMAGE_FILE_PATH, ok_filepath))
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
        image.save(filepath, quality=settings.IMAGE_QUALITY)

    return x_accel_response("/images/square/{}/{}".format(max_length, ok_filepath))


@app.route("/width/<int(min=50,max=2000):max_length>/<filename>", methods=["GET"])
def width_fit_media(max_length, filename):
    if not is_image(filename):
        return full_media(filename)

    ok_filepath = generate_file_path(filename)
    filepath = os.path.join(settings.IMAGES_FILE_PATH, "width/{}/{}".format(max_length, ok_filepath))
    if not os.path.exists(filepath):
        try:
            image = Image.open(os.path.join(settings.FULL_IMAGE_FILE_PATH, ok_filepath))
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
        image.save(filepath, quality=settings.IMAGE_QUALITY)

    return x_accel_response("/images/width/{}/{}".format(max_length, ok_filepath))


if __name__ == '__main__':
    app.run()
