#! /usr/bin/python
import sys, re, time, datetime, random
from datetime import datetime
from time import gmtime
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import models, transaction
from email.Parser import Parser
from django.conf import settings
from django.db import connection

from www.models import DictionaryEntry, Questions, Contact, Responses, PendingEvents
from util.sms import SMS

logfile = open("/var/wordisms/log/incoming", "a+")
def logger(message):
    message = time.strftime("%m\%d\%Y %H:%M:%S", time.gmtime()) + " " + message
    logfile.write("%s\n" % message)
    print "%s" % message

def get_plaintext(email_message):
    for part in email_message.walk():
        if part.get_content_type() == 'text/plain':
            return part.get_payload()
    raise Exception, ("Message payload not found: '%s'" % (email_message))

def validate_command(plaintext):
    if plaintext in ['1', '2', '3', '4', 'signup', 'stats', 'help', 'howto', 'quit', 'resend']:
        return plaintext
    raise Exception, ("invalid command: '%s'" % plaintext)

def parse_command(command):
    tokens = command.split()
    return [ tokens[0] , tokens[1:] ]

def get_sender(email_message):
    try:
        return re.findall( re.compile("[-a-zA-Z0-9._]+@[-a-zA-Z0-9_]+.[a-zA-Z0-9_.]+"), email_message.get('From') )[0]
    except Exception:
        raise Exception, ("Invalid email address in: '%s'" % (email_message.get('From')))

#define actions
def do_quit(contact):
    message = "Thanks for helping us make WordiSMS better. Text back 'signup' at any time to start receiving questions again!"
    SMS(contact.address, message).send()
    contact.delete()

def do_help(contact):
    help_email = "You'll get a definition and 4 words, send back just the # of the word that you think is correct. Send 'stats' for progress 'quit' to leave"
    logger("Message: (%s) %s" % (len(help_email),help_email))
    SMS(contact.address, help_email).send()

def do_stats(contact):
    message = contact.get_stats()
    logger(message)
    SMS(contact.address, message).send()

def do_answer(contact, response):
    """
    Takes a Question for the sender's contact and creates a Response with
    the user's response (accepts 1, 2, 3, or 4)
    """
    logger("Command entered: %s" % response)
    if PendingEvents.objects.filter(contact=contact):
        #TODO I'm sleepy, is this kosher?
        logger("Already a pending event for '%s'" % contact)
        raise PendingEvents.IntegrityError

    question = Questions.objects.get(contact=contact)
    word = { 
        '1': lambda x: x.one,
        '2': lambda x: x.two,
        '3': lambda x: x.three,
        '4': lambda x: x.four
    }[response](question)
    Responses( definition=question.correct,
               word=word,
               contact=contact).save()
    question.delete()

def do_feedback(contact, message):
    logger("Entering do_feedback (%s, %s)" % (contact, message))
    
def do_token(contact):
    SMS(contact.address, "Your token is %s" % contact.token).send()

def do_invalid_command(contact):
    error_message = "Sorry! We didn't understand that command. Make sure you're sending a number (like 3) or one of our command words (like 'help'"
    SMS(contact.address, error_message).send()

def do_new_question(contact):
    cursor = connection.cursor()
    cursor.execute("select id from www_dictionaryentry where id not in (select word_id from www_responses submitted where contact_id=%s) order by rand() limit 1", [contact.id])
    row = cursor.fetchone()
    logger("Selected word, uid %s" % (row))
    word_id = row[0]
    cursor.execute("select t1.id from www_dictionaryentry t1 where t1.id != %s order by rand() limit 3", [word_id]);
    choices_ids = cursor.fetchall()
    #   return (word_id,) , random.shuffle(map(lambda x: x[0], choices_ids)+[word_id])
    choices = map(lambda x: x[0], choices_ids)+[word_id]
    random.shuffle(choices)

    correct = DictionaryEntry(id=word_id)
    one     = DictionaryEntry(id=choices[0])
    two     = DictionaryEntry(id=choices[1])
    three   = DictionaryEntry(id=choices[2])
    four    = DictionaryEntry(id=choices[3])

    Questions(contact=contact,correct=correct,one=one,two=two,three=three,four=four).save()
    do_send_question(contact)

def do_resend(contact):
    return do_send_question(contact)

def do_send_question(contact):
    PendingEvents(contact=contact).save()

@transaction.commit_manually
def parse_new_email(email_message):
    try:
        plaintext = get_plaintext(email_message).strip().lower()
        if not plaintext:
            command = "signup"
        else:    
            (command, params) = parse_command(plaintext)
        sender = get_sender(email_message)
        logger("Entering parse_new_email, command (%s), sender (%s)" % ( command , sender))

        # the only special case
        # this is the only valid action you can take when not in the system
        if command == "signup" or not command:
            try:
                token = random.randint(10000,99999)
                contact = Contact(address=sender,token=token,type="email")
                contact.save()
                command = "new_question"
                logger("created new contact: %s" % str(contact))
                signup_email = ("Thanks for signing up! Your token for the web site is %s, but you should receive a question in a second. Send 'help' for instructions." % token)
                logger("Message: (%s) %s" % (len(signup_email),signup_email))
                SMS(contact.address, signup_email).send()
            except:
                logger("* Contact already exists: %s" % str(contact))
                contact = Contact.objects.get(address=sender)
                command = "send_question"
        else:    
            contact = Contact.objects.get(address=sender)

        # response numbers don't have individual functions, so handle them separately
        #TODO this hits some weirdness if you get a response while there is a pending event
        if command >= '1' and command <= '4':
            do_answer(contact,command)
            command = "new_question"

        if 'do_'+command not in globals():
            raise KeyError, "do_%s command not found" % command
        logger("Entering do_%s (contact: %s)" % (command, contact))
        # this is why I love Python
        globals()['do_'+command](contact)
        logger("Exiting do_%s" % command)

        transaction.commit()
        logger("Transaction committed")
    except KeyError:
        logger("* Did not understand command '%s'" % command)
        logger("* Full message: '%s'" % plaintext)
        do_invalid_command(contact)
    except Contact.DoesNotExist:
        logger("* Could not find '%s' in the database. No action taken." % sender)
        #SMS(sender, "Text back 'signup' to join WordiSMS!'").send()
    except Exception:
        transaction.rollback()
        logger("Transaction rolled back")
        raise

if __name__ == "__main__":
    logger("Entering incoming.py")
    parse_new_email( Parser().parse(sys.stdin) )
