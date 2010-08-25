from django.db import models
import datetime
from django.contrib.auth.models import User

class Struct:
        def __init__(self, **entries): self.__dict__.update(entries)

class WordismsUser(models.Model):
    user = models.ForeignKey(User,unique=True)
    def __unicode__(self):
        return str(self.user)       
    def get_stats(self):
        for contact in Contact.objects.filter(wordisms_user=self):
            # do something more meaningful here
            contact.get_stats()
    # this will eventually hold more information about the user
    # right now it's just a mapping between auth_user and contact
    # more or less it's an extension of www_auth

class Contact(models.Model):
    address = models.CharField(max_length=50)
    type = models.CharField(max_length=25)
    class Meta:
        unique_together = ('address', 'type')
    verbose = models.BooleanField(default=False)
    time_created = models.DateTimeField(auto_now_add=True)
    token = models.PositiveIntegerField(default=0)
    wordisms_user = models.ForeignKey(WordismsUser,null=True)
    def __unicode__(self): 
        return str(self.id) + ", " + \
               str(self.address) + ", " + \
               str(self.verbose) + ", " + \
               str(self.time_created) + ", " + \
               str(self.token)
    def get_user(self):
        if self.wordisms_user:
            return self.wordisms_user
        return DummyWordismsUser(self)
    def get_stats(self):
        responses = Responses.objects.filter(contact=self)
        total = 0
        correct = 0
        for response in responses:
            total += 1
            correct += (response.word_id == response.definition_id)
        result = "%s correct out of %s" % (correct,total)
        if total > 0: result += " (%s%%)" % (100*correct/total)
        return result
    def get_wrong_answers(self):
        responses = Responses.objects.filter(contact=self)
        wrong_answers = []
        for response in responses:
            if (response.word_id != response.definition_id):
                # [their answer, actual answer]
                # TODO can we make this a class on the fly
                #  so that we can append anonymous structs, and then
                #  for a in  wrong_answers: print a.word, a.definition
                wrong_answers.append( Struct(attempt=DictionaryEntry.objects.get(id=response.word_id).word,
                                          definition=DictionaryEntry.objects.get(id=response.definition_id).definition,
                                                word=DictionaryEntry.objects.get(id=response.definition_id).word,
                                           timestamp=response.timestamp))
#                wrong_answers.append([
#                    DictionaryEntry.objects.get(id=response.word_id).word, 
#                    DictionaryEntry.objects.get(id=response.definition_id).definition,
#                    DictionaryEntry.objects.get(id=response.definition_id).word,
#                    response.timestamp ])
        return wrong_answers        

class DummyWordismsUser(WordismsUser):
    """If the contact is not linked to the account, he still needs a WordismsUser"""
    def __init__(self,contact):
        WordismsUser.__init__(self)
        self.contact = contact
    def __unicode__(self):
        return str(self.id) + ", " + str(self.contact)

class Wordlist(models.Model):
    creator = models.ForeignKey(User, related_name='creator_uid')
    name = models.CharField(max_length=25)
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=(('defs',)*2, ('quiz',)*2), default='defs')
    def __unicode__(self):
        return str(self.name) + ", " + str(self.creator)

class Subscription(models.Model):
    wordisms_user = models.ForeignKey(WordismsUser)
    wordlist = models.ForeignKey(Wordlist)
    timestamp = models.DateTimeField(auto_now_add=True) 
    def __unicode__(self):
        return "WordismsUser_id: %s, %s" % (str(self.wordisms_user.id), str(self.wordlist.name))
        #        return str(Wordlist.objects.get(id=self.wordlist))

class DictionaryEntry(models.Model):
    wordlist = models.ForeignKey(Wordlist)
    word = models.CharField(max_length=20)
    definition = models.CharField(max_length=100)
    def __unicode__(self):
        return "[%s] %s,%s" % (self.id, self.word, self.definition)

class QuizEntry(models.Model):
    correct = models.ForeignKey(DictionaryEntry, related_name="correct_dictionaryentry")
    wrong1 = models.ForeignKey(DictionaryEntry, related_name="wrong1_dictionaryentry")
    wrong2 = models.ForeignKey(DictionaryEntry, related_name="wrong2_dictionaryentry")
    wrong3 = models.ForeignKey(DictionaryEntry, related_name="wrong3_dictionaryentry")
    def __unicode__(self):
        return "(>%s<, %s, %s, %s)" % (self.correct, self.wrong1, self.wrong2, self.wrong3)

class Responses(models.Model):
    timestamp  = models.DateTimeField(auto_now_add=True)
    definition = models.ForeignKey(DictionaryEntry, related_name="definition_id")
    word       = models.ForeignKey(DictionaryEntry, related_name="word_id")
    contact    = models.ForeignKey(Contact)
    def __unicode__(self): 
        return str(self.timestamp) + ", " + \
               self.definition + ", " + self.word

class PendingEvents(models.Model):
    contact = models.ForeignKey(Contact)
    time = models.DateTimeField(auto_now=True)
    def __unicode__(self): 
        return str(user) + ', ' + str(time)

class Questions(models.Model):
    contact  = models.ForeignKey(Contact)
    correct  = models.ForeignKey(DictionaryEntry, related_name='correct')
    one      = models.ForeignKey(DictionaryEntry, related_name='1_word_uid')
    two      = models.ForeignKey(DictionaryEntry, related_name='2_word_uid')
    three    = models.ForeignKey(DictionaryEntry, related_name='3_word_uid')
    four     = models.ForeignKey(DictionaryEntry, related_name='4_word_uid')
    time_created = models.DateTimeField(auto_now_add=True)

