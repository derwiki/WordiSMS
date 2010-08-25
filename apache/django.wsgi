import site
site.addsitedir("/var/wordisms/")
site.addsitedir("/var/wordisms/www")

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'www.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
