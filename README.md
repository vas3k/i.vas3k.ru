# i.vas3k.ru 

### Old and simple script which helps me to upload, resize and insert pictures to my blog 

Does many handy things using a bit of nginx X-Accel-Redirect magic. Can resize pictures on the go and distribute the final result through nginx.

Written on Flask. Uses Pillow for image processing and PostgreSQL for statistics. Yes, the usage of postgres here is overkill, but the previous version on plain-files constantly became inconsistent and I rewrote everything.

Almost all logic sits in one file (app.py). Also see settings.py before you go. Images can be uploaded through a simple web-interface (sits on the root) or using any script. Works both with multipart-form-data files and raw bytes uploading.

Here is some examples how everything works:

* http://i.vas3k.ru/32p.jpg — canonical image URL. Returns an image resized to an universal width. See COMMON_IMAGE_LENGTH in settings;
* http://i.vas3k.ru/full/32p.jpg — original image file;
* http://i.vas3k.ru/500/32p.jpg — resized to 500px by the longest side. Min = 50, max = 20000;
* http://i.vas3k.ru/width/500/32p.jpg — resized to 500px by the width. For convenient tiling or background usage;
* http://i.vas3k.ru/square/500/32p.jpg — cropped to the square in the center;
