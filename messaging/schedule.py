from time import sleep, gmtime
from www.main.models import PendingEvents

#d = strftime("%Y-%m-%d %H:%M:%S", gmtime(time()+50000))
#PendingEvents(user=t, time=d).save()


#class PendingEvents(models.Model):
#    user = models.ForeignKey(User, related_name='user')
#    time = models.DateTimeField()

#class User(models.Model):
#    phonenumber = models.CharField(max_length=25)
#    start_time = models.TimeField()
#    end_time = models.TimeField()
#    interval = models.PositiveIntegerField()
#    activated = models.BooleanField()

# time.strptime("04:00", "%H:%M")

# User(phonenumber='6503059225@tmomail.net', start_time=datetime.time(4, 0), end_time=datetime.time(4, 0), interval=20, activated=False).save()

while True:
    PendingEvents.objects.filter(time<strftime("%Y-%m-%d %H:%M:%S", gmtime()))
    sleep(1)
