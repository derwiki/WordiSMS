from django.shortcuts import render_to_response
from www.models import WordismsUser, Contact, Responses, Subscription, Wordlist, DictionaryEntry
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.template import RequestContext
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
import csv

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()

    def clean(self,*args, **kwargs):
        return super(UploadFileForm, self).clean(*args, **kwargs)

class SignupForm(forms.Form):
    username = forms.CharField(max_length=100, label="Username")
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False),min_length=6,max_length=100,label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False),min_length=6,max_length=100,label="Verify")
    email = forms.EmailField(label="Email")

    def clean_username(self):
        if not 'username' in self.data:
            return None
        if User.objects.filter(username=self.data['username']):
            raise forms.ValidationError("Username already exists")
        return self.data['username']

    def clean_email(self):
        if not 'email' in self.data:
            return None
        if User.objects.filter(username=self.data['email']):
            raise forms.ValidationError("Email already exists")
        return self.data['email']

    def clean_password(self):
        if not 'password' in self.data:
            return None
        if self.data['password1'] != self.data['password2']:
            raise forms.ValidationError('Passwords are not the same')
        return self.data['password1']
                                        
    def clean(self,*args, **kwargs):
        self.clean_username()
        self.clean_email()
        self.clean_password()
        return super(SignupForm, self).clean(*args, **kwargs)
                                                                

def account_signup(request):
    if request.method == "POST":
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            user = User(username=signup_form.cleaned_data['username'],
                        email=signup_form.cleaned_data['email'])
            user.set_password(signup_form.cleaned_data['password1'])
            user.save()
            user = authenticate(username=user.username,password=signup_form.cleaned_data['password1'])
            login(request, user)
	    #TODO dunno why this doesn't work, but it's not important
            #request.user.messsage_set.create(message="Time to kick ass and take names -- you're all set up!")
            return HttpResponseRedirect('/account')
    return render_to_response('account/signup.html', { 'signup_form': SignupForm(request.POST) })

def index(request):
    user = None
    if request.user.is_authenticated():
        user = request.user
    return render_to_response('index.html', {'user': user},
                              context_instance=RequestContext(request))

def user_stats(request, user_id):
    return render_to_response('user/stats.html', { 'user': User.objects.get(id=user_id) },
                              context_instance=RequestContext(request))
"""
def wordlist(request, wordlist_id):    
    wordlist = Wordlist.objects.get(id=wordlist_id)
    return render_to_response('wordlist.html', { 'wordlist': wordlist,
                                                 'entries': DictionaryEntry.objects.order_by('word').filter(wordlist=wordlist)},
                              context_instance=RequestContext(request))
"""
@login_required
def wordlist_list(request):
    if "wordlist_id" in request.POST:
        # populate or create WordismsUser
        try:
            wordisms_user = WordismsUser.objects.get(user=request.user)
        except WordismsUser.DoesNotExist:
            wordisms_user = WordismsUser(user=request.user)
            wordisms_user.save()

        try:
            #TODO make sure you can't subscribe to the same word list twice
            wordlist_id = request.POST['wordlist_id']
            wordlist = Wordlist.objects.get(id=wordlist_id)
            subscription = Subscription(wordisms_user=wordisms_user,wordlist=wordlist)
            subscription.save()
            request.user.message_set.create(message=("Subscribed to '%s'" % wordlist.name))
            return HttpResponseRedirect("/account")
        except Wordlist.DoesNotExist:
            request.user.message_set.create(message=("Internal error, could not find wordlist id %s" % wordlist_id))
            return HttpResponseRedirect("/wordlist/list")

    return render_to_response(  'wordlist_list.html', 
                              { 'wordlists': Wordlist.objects.order_by('name') },
                              context_instance=RequestContext(request) )

@login_required
def user_list(request):
    return render_to_response('user/list.html', { 'users': User.objects.all() },
                              context_instance=RequestContext(request))

@login_required
def contact_all(request):
    return render_to_response('contact/all.html', { 'contacts': Contact.objects.all() },
                               context_instance=RequestContext(request))

@login_required    
def contact_report(request, contact_id):    
    if not Contact.objects.filter(id=contact_id):
        #TODO something about this doesn't feel right
        user.message_set.create(message="Invalid contact ID")
        return render_to_response('contact/report.html', {}, 
                                  context_instance=RequestContext(request))
    wrong_answers = Contact.objects.get(id=contact_id).get_wrong_answers()

    return render_to_response('contact/report.html', { 'wrong_answers': wrong_answers },
                               context_instance=RequestContext(request))

@login_required 
def account_claim_token(request):
    try:
        contact = Contact.objects.get(token=request.GET['token'])
    except:
        request.user.message_set.create(message=("Sorry %s, we can't seem to find the token %s" % (request.user.username, request.GET['token'])))
        return HttpResponseRedirect("/account")

    try:
        wordisms_user = WordismsUser.objects.get(user=request.user)
    except:
        # create wordisms_user if it doesn't already exist
        wordisms_user = WordismsUser(user=request.user)
        wordisms_user.save()

    contact.wordisms_user = wordisms_user
    contact.token = 0
    # token has been claimed, free it
    contact.save()
    request.user.message_set.create(message='Device using "%s" was successfully linked to your account' % contact.address)
    return HttpResponseRedirect("/account")

@login_required
def account(request):
    try:
        wordisms_user = WordismsUser.objects.get(user=request.user)
    except:
        request.user.message_set.create(message="You have no interfaces linked to your account.")
        return render_to_response('account/index.html', {}, context_instance=RequestContext(request))

    if 'contact_id' in request.POST:
        #TODO make sure this will only delete contact IDs for the current account
        try:
            contact = Contact.objects.get(id=request.POST['contact_id'])

            if contact.wordisms_user != wordisms_user:
                raise Exception
            contact.wordisms_user = None
            contact.save()
            request.user.message_set.create(message=("Unlinked device %s (id %s)" % (contact.address,contact.id)))
        except Contact.DoesNotExist:
            request.user.message_set.create(message=("Internal error, could not find id %s" % request.POST['contact_id']))
        except:
            request.user.message_set.create(message=("Internal error, %s was not linked to your account" % contact.address))
        # redirect so that a refresh won't repost the word list
        return HttpResponseRedirect("/account")


    if 'subscription_id' in request.POST:
        #TODO make sure this will only delete contact IDs for the current account
        try: 
            subscription_id = request.POST['subscription_id']
            subscription = Subscription.objects.get(id=subscription_id,wordisms_user=wordisms_user)
            subscription.delete()

            request.user.message_set.create(message=("Unlinked wordlist (id %s)" % subscription.wordlist.id))
            if not Subscription.objects.filter(wordisms_user=wordisms_user):
                request.user.message_set.create(message=("There are no more word lists linked to your account"))
        except Subscription.DoesNotExist:
            request.user.message_set.create(message=("Internal error, could not find subscription_id %s" % subscription_id))
#        except:
#            request.user.message_set.create(message=("Internal error, %s was not linked to your account" % subscription.wordlist.name))
        # redirect so that a refresh won't repost the word list
        return HttpResponseRedirect("/account")

    if 'wordlist_id' in request.POST:
        try:
            wordlist = Wordlist.objects.get(id=request.POST['wordlist_id'])
            if wordlist.creator != request.user:
                raise Exception 
            request.user.message_set.create(message=("Deleted wordlist '%s' (id %s)" % (wordlist.name, wordlist.id)))
            wordlist.delete()
        except Wordlist.DoesNotExist:
            request.user.message_set.create(message=("Internal error, could not find wordlist_id %s" % request.POST['wordlist_id']))
        except Exception:
            request.user.message_set.create(message=("You didn't create '%s' so you can't delete it!" % wordlist.name))

        # redirect so that a refresh won't repost the word list
        return HttpResponseRedirect("/account")

    if 'file' in request.FILES:
        print "entering this block"
        form = UploadFileForm(request.POST, request.FILES)
#        if form.is_valid():
        file = request.FILES['file']
#        print "file %\n" % file
        rows = csv.reader(file)
        wordlist = Wordlist(name=request.POST['title'], creator=request.user)
        wordlist.save()
        request.user.message_set.create(message=("Created wordlist '%s'" % wordlist.name))

        subscription = Subscription(wordlist=wordlist,wordisms_user=wordisms_user)
        subscription.save()
        request.user.message_set.create(message=("You are now subscribed to '%s'" % wordlist.name))

        for row in rows:
            print "%s,%s" % (row[0], row[1])
            dictionary_entry = DictionaryEntry(word=row[0], definition=row[1], wordlist=wordlist)
            dictionary_entry.save()

        request.user.message_set.create(message=("Populated new wordlist '%s'" % wordlist.name))
        # redirect so that a refresh won't repost the word list
        return HttpResponseRedirect("/account")

    contacts = Contact.objects.filter(wordisms_user=wordisms_user)
    responses, subscriptions = {} , {}
    for contact in contacts:
        responses[contact.id] = Responses.objects.filter(contact=contact)

    subscriptions = Subscription.objects.order_by('id').filter(wordisms_user=wordisms_user)
    return render_to_response('account/index.html', { 'user': request.user,
                                                      'wordisms_user': wordisms_user,
                                                      'contacts': contacts,
                                                      'responses': responses,
                                                      'subscriptions': subscriptions,
                                                      'file_upload_form': UploadFileForm()},
                              context_instance=RequestContext(request))
