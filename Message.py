import sys, time, datetime, random, re
from time import gmtime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import models, transaction
from django.db import connection
from email.Parser import Parser

from www.main.models import Dictionary, Questions, User, Submitted, PendingEvents
from www.util.sms import SMS

class Message:
    
    #define actions
    def do_signup(sender, interval):
        logger("Entering do_signup (%s)" % (sender))
        try:
            try:
                user = User(phonenumber=sender,interval=int(interval))
            except (ValueError, IndexError):
                user = User(phonenumber=sender)
            user.save()
        except:
            logger("user already exists! %s" % sender)
            #TODO send a message back? fail silently?
            #raise Exception, "User '%s' already exists" % sender
            raise
            return
        signup_email = "Thank you for signing up! How to play: we will send you a message listing a definition and a choice of four words. You must choose the correct word corresponding to that definition. Respond with only the number of the word that you believe is correct. Text 'stats' to see how you're doing and 'quit' to leave WordiSMS."
        SMS(user.phonenumber, signup_email).send()
        logger("Exiting do_signup")
        return

    def do_quit(sender):
        logger("Entering do_quit (%s)" % (sender))
        user = User.objects.get(phonenumber=sender)
        message = "Thanks for helping us make WordiSMS better. Text back 'signup' at any time to start receiving questions again!"
        SMS(user.phonenumber, message).send()
        user.delete()
        logger("Exiting do_quit");
        return

    def do_help(sender):
        logger("Entering do_help (%s)" % (sender))
        user = User.objects.get(phonenumber=sender)
        help_email = "How to play: we will send you a message listing a definition and a choice of four words. You must choose the correct word corresponding to that definition. Respond with only the number of the word that you believe is correct. Text 'stats' to see how you're doing and 'quit' to leave WordiSMS."
        logger("Message: %s" % (help_email))
        SMS(user.phonenumber, help_email).send()
        logger("Exiting do_help");
        return

    def do_stats(sender):
        logger("Entering do_stats (%s)" % (sender))
        user = User.objects.get(phonenumber=sender)

        cursor = connection.cursor()
        cursor.execute("SELECT count( 1 ) FROM `main_submitted` WHERE def_uid_id = word_uid_id AND user_uid_id = %s", [user.id])
        number_correct = cursor.fetchone()[0]
        logger("Number right: %s" % (number_correct))
        cursor.execute("SELECT count( 1 ) FROM `main_submitted` WHERE user_uid_id = %s", [user.id])
        number_total = cursor.fetchone()[0]
        if number_total == 0:
            message = "You haven't answered any questions yet! Text 'help' for instructions on how to use WordiSMS"
        else:
            logger("Total number: %s" % (number_total))
            percentage_correct = float(number_correct) * 100 / number_total
            logger("Percentage correct: %d" % (percentage_correct))
            message = "You have answered %s out of %s correct (%d%%)" % (number_correct, number_total, percentage_correct)
        logger(message)
        SMS(user.phonenumber, message).send()
        logger("Exiting do_stats");
        return

    def do_answer(sender, response):
        logger("Entering do_answer (%s, %s)" % (sender, response))
        user = User.objects.get(phonenumber=sender)
        if len(PendingEvents.objects.filter(user=user)) != 0:
            raise Exception, ("Already a pending event for '%s'" % (sender))

        word_uid = { 
            '1': lambda x: x.one,
            '2': lambda x: x.two,
            '3': lambda x: x.three,
            '4': lambda x: x.four
        }[response](Questions.objects.get(user=user))
        user = User.objects.get(phonenumber=sender)
        #print "%s %s" % (word_uid.id, Questions.objects.get(user=user).correct.id)
        question = Questions.objects.get(user=user)
        rc = Submitted(def_uid=question.correct,word_uid=word_uid,user_uid=user).save()
        logger("Submitted() rc: %s" % rc) 
        rc = question.delete()
        logger("question.delete() rc: %s" % rc) 
        logger("Exiting do_answer");

    def do_invalid_command(sender, command):
        logger("Entering do_invalid_command (%s, %s)" % (sender, command))
        user = User.objects.get(phonenumber=sender)
        message = "Oops! Sorry, we didn't recognize that command. Please try again! Reply with 'howto' for instructions."
        SMS(user.phonenumber, message).send()
        logger("Exiting do_invalid_command")
        return

    def do_new_question(sender):
        logger("Entering do_new_question (%s)" % (sender))
        user = User.objects.get(phonenumber=sender)
        cursor = connection.cursor()
        cursor.execute("select id from main_dictionary where id not in (select word_uid_id from main_submitted submitted where user_uid_id=%s) order by rand() limit 1", [user.id])
        row = cursor.fetchone()
        logger("Selected word, uid %s" % (row))
        word_id = row[0]
        cursor.execute("select t1.id from main_dictionary t1 where t1.id != %s order by rand() limit 3", [word_id]);
        choices_ids = cursor.fetchall()
        #   return (word_id,) , random.shuffle(map(lambda x: x[0], choices_ids)+[word_id])
        choices = map(lambda x: x[0], choices_ids)+[word_id]
        random.shuffle(choices)

        correct = Dictionary(id=word_id)
        one     = Dictionary(id=choices[0])
        two     = Dictionary(id=choices[1])
        three   = Dictionary(id=choices[2])
        four    = Dictionary(id=choices[3])

        question = Questions(user=user,correct=correct,one=one,two=two,three=three,four=four)
        rc = question.save()
        logger("question.save() rc %s" % rc)

        new_time = time.strftime("%Y-%m-%d %H:%M", gmtime(time.time()+ 60 * user.interval) )
        pending_event = PendingEvents(user=user, time = new_time)
        rc = pending_event.save()
        logger("pending_event.save() rc %s" % rc)
        logger("Exiting do_new_question");
        return

    @transaction.commit_manually
    def parse_new_email(message):
        logger("entering parse_new_email")
        try:
            sender = get_sender(message)
            (command, params) = parse_command(message.strip().lower())

            logger("entering rpc router: %s, %s" % (command, params))
            if command == 'signup':
                logger("len(params): %s" % (len(params)))
                if len(params) > 0:
                    do_signup(sender, params[0])
                else:
                    do_signup(sender, 0)
                transaction.commit()
                do_new_question(sender)
            elif command == 'quit':
                do_quit(sender)
            elif command == 'help' or command == 'howto':
                do_help(sender)
            elif command == 'stats':
                do_stats(sender)
            elif command >= '1' and command <= '4':
                do_answer(sender, command)
                do_new_question(sender)
            else:
                do_invalid_command(sender, command)

            transaction.commit()
            logger("Transaction committed")
        except Exception:
            transaction.rollback()
            logger("Transaction rolled back")
            raise

class MessageSMS(Message):
    sender = None
    command = None
    params = None

    def __init__(self, email_message):
#        print email_message
        for part in email_message.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload()
                break

        print email_message.get('From')
        self.sender = re.findall( re.compile("[-a-zA-Z0-9._]+@[-a-zA-Z0-9_]+.[a-zA-Z0-9_.]+"), email_message.get('From') )[0]
        tokens = payload.split()
        self.command = tokens[0]
        self.params = tokens[1:]
        
    def __repr__(self):
        return "\n".join([self.sender, self.command, self.params])

        
message = MessageSMS ( Parser().parse(sys.stdin) )
print message
