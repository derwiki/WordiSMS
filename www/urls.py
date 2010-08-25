from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import login,logout
from www.models import DictionaryEntry, Wordlist
from django.views.generic import list_detail, simple
from django.http import Http404

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
# test line

urlpatterns = patterns('www.views',
#'django.views.generic.simple',
    (r'^account/login/?$', login,
                           {'template_name': 'account/login.html' }),
    (r'^account/logout/?$', logout, 
                            {'template_name': 'account/logout.html' }),

    (r'^account/signup/?$', 'account_signup'),
    (r'^account/claim_token/?$', 'account_claim_token'),

    (r'^user/(\d+)/stats$', 'user_stats'),
    (r'^user/list$', 'user_list'),

    (r'^contact/all/?$', 'contact_all'),
    (r'^contact/report/(\d+)/?$', 'contact_report'),

    (r'^account/?$', 'account'),

    (r'^/?$', 'index'),

    (r'^wordlist/list/?$', 'wordlist_list')
)

def wordlist_by_id(request, wordlist_id):
    # Look up the wordlist (and raise a 404 if it can't be found).
    try:
        wordlist = Wordlist.objects.get(id=wordlist_id)
    except Wordlist.DoesNotExist:
        raise Http404

    # Use the object_list view for the heavy lifting.
    return list_detail.object_list(
        request,
        queryset = DictionaryEntry.objects.order_by('word').filter(wordlist=wordlist),
        template_name = "wordlist.html",
#TODO why doesn't this work?
#        template_object_name = "entries",
        extra_context = {"wordlist" : wordlist }
    )

urlpatterns += patterns('',
    (r'^wordlist/(?P<wordlist_id>\d+)/view/?$', wordlist_by_id),
)

if settings.DEBUG:
    urlpatterns += patterns('django.views',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            'static.serve', {'document_root': settings.MEDIA_ROOT}))
