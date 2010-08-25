import os

class SMS:

    _FROM_ADDRESS = "WordiSMS <study@wordisms.org>"

    _SENDMAIL = "/usr/sbin/sendmail" # sendmail location

    _to = ""

    _subject = ""

    _body = ""
  
#    def __init__(self, to, subject, body):

#        print "in init"

        # Only for users of actual mail clients
#        self._subject = subject

#        __init__(self, to, body)

    def __init__(self, to, body, subject=""):

        self._to = [to]

        self._subject = subject

        self._body = body

    def send(self):

#        print "from: ", self._FROM_ADDRESS
#        print "subject: ", self._subject
#        print "to: ", self._to
#        print "body: ", self._body

        # Prepare actual message
        self._message = (
            'From: %s\n'
            'To: %s\n'
            'Subject: %s\n'
            'Return-Path: study@wordisms.org'
            '\n'
            '%s\n'
            ) % (self._FROM_ADDRESS, ",".join(self._to), self._subject, self._body)

        # Send the mail
#        log(self._message)

        p = os.popen("%s -f study@wordisms.org -t -i" % self._SENDMAIL, "w")
        p.write(self._message)

        status = p.close()
        return status
