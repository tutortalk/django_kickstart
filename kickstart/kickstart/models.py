from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    about = models.TextField(null=True, blank=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __unicode__(self):
        return u"{0} - {1} - {2}".format(self.user.username, self.last_name, self.first_name)
