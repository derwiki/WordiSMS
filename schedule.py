#! /usr/bin/python
import os, sys, traceback, re

from django.core.management import setup_environ

import settings
setup_environ(settings)

from www.models import PendingEvents
from util.sms import SMS
from time import sleep, gmtime, strftime
from string import lstrip, rstrip

from django.db import connection

log_file = open("/var/wordisms/log/schedule", "a+")

_QUESTION_SUBJECT = "Re: New question from WordiSMS!"

#class Incoming:

# TODO: Abstract log functionality into independent script
def log(message):
    log_file.write(strftime("%m\%d\%Y %H:%M:%S", gmtime()) + " " + message + "\n")
#    print message

def construct_message_body(user_id, QA):

    BODY = ''

    last = get_last_submission(user_id)
    if last:
        (def_uid, word_uid, correct_word) = last[0]
        if (def_uid == word_uid):
            BODY += "Correct!\n"
        else:
            BODY += "Wrong, it was %s.\n" % lstrip(rstrip(correct_word))

    BODY += ('%s\n'
        '1)%s\n'
        '2)%s\n'
        '3)%s\n'
        '4)%s\n') % QA
#            'To which word does this definition correspond? Responsd with only the number denoting your answer.\n'

    return BODY

def prep_for_sms(body):
    return body.replace('\n', ' ')

# def send_sms(user_id, dest_address, QA):
#     SENDMAIL = "/usr/sbin/sendmail" # sendmail location

#     # TODO: What do we put?
#     FROM = "WordiSMS <study@wordisms.org>"
#     TO = [dest_address]

#     # TODO: What do we put?
#     SUBJECT = "Wordisms Question"

#     BODY = construct_message_body (user_id, QA)

#     # Prepare actual message
#     message = (
#         'From: %s\n'
#         'To: %s\n'
#         '\n'
#         '%s\n'
#         ) % (FROM, ",".join(TO), BODY)
#     log(message)

#     # Send the mail
#     p = os.popen("%s -t -i" % SENDMAIL, "w")
#     p.write(message)
#     status = p.close()
#     return status

def poll_pending_events():
    for row in get_pending_events():
        # Error-check time range and fix the pendingevent for the next available range ... ?
        # TODO: Create a wrapper object to properly store array "row"?
#        log(str(row))

        sms = None
        if (is_email_address(row[2])):
            # TODO: Send "re:" only on subsequent e-mails, not the first one
            sms = SMS(row[2], construct_message_body(row[1], row[3:8]), _QUESTION_SUBJECT)
        else:
            # TODO: Include a "prep_for_sms" compaction function in the SMS class
            sms = SMS(row[2], prep_for_sms(construct_message_body(row[1], row[3:8])))
        status = sms.send()
        # send_sms (user_id, dest_address, QA)
        # sms = SMS(row[2], construct_message_body(row[1], row[3:8]))
        # status = send_sms(row[1], row[2], row[3:8])
        if status:
        # throw error
            log("Sendmail error occurred with exit status = " + status)
            raise LookupError (status, row)
        else:
            delete_pending_event(row[0])

def is_email_address(dest_address):
    # (?:)
    if re.findall(re.compile("[-a-zA-Z0-9._]+@(gmail|hotmail|live).[a-zA-Z0-9_.]+"), dest_address):
        return True
    return False           

def get_pending_events():
# returns - tuple with format following the values following the "SELECT" keyword in the 
# following database call
    cursor = connection.cursor()
    sql = ('SELECT www_pendingevents.id, www_contact.id, www_contact.address, correct.definition, one.word, two.word, three.word, four.word '
           'FROM www_pendingevents '
           'JOIN www_contact ON (www_pendingevents.contact_id = www_contact.id) '
           'JOIN www_questions ON (www_questions.contact_id = www_contact.id) '
           'JOIN www_dictionaryentry correct ON (correct.id = www_questions.correct_id) '
           'JOIN www_dictionaryentry one ON (one.id = www_questions.one_id) '
           'JOIN www_dictionaryentry two ON (two.id = www_questions.two_id) '
           'JOIN www_dictionaryentry three ON (three.id = www_questions.three_id) '
           'JOIN www_dictionaryentry four ON (four.id = www_questions.four_id) '
           'WHERE www_pendingevents.time < now()')
    cursor.execute(sql)
    return cursor.fetchall()

def get_last_submission(user_id):
# returns - tuple with format following the values following the "SELECT" keyword in the 
# following database call
    cursor = connection.cursor()
    sql =('SELECT word.id, definition.id, definition.word '
                    'FROM www_responses '
                    'JOIN `www_dictionaryentry` `definition` ON (definition.id = www_responses.definition_id) '
                    'JOIN `www_dictionaryentry` `word` ON (word.id = www_responses.word_id) '
                    'WHERE contact_id=%s '
                    'ORDER BY www_responses.id DESC '
                    'LIMIT 1') % (user_id)
#    print "sql = ", sql
    cursor.execute(sql)
    return cursor.fetchall()

def delete_pending_event(pe_id):
    try:
        p = PendingEvents.objects.get(id=pe_id)
        p.delete()
    except Exception, inst:
        log("Exception with PendingEvents!!!")
        log(str(type(inst)))
        log(str(inst.args))

def main():
# Execution begins here:

    log("Running...")

    try:
        poll_pending_events()
    except Exception, detail:
        log("Exception!!!")
        log(str(detail))

    log("Done.")

if __name__ == "__main__":
    main()
#    sys.exit(main())
