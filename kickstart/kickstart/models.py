from django.db import models
from django.contrib.auth.models import User
from pytils.translit import slugify
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    about = models.TextField(null=True, blank=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __unicode__(self):
        return u"{0} - {1} - {2}".format(self.user.username, self.last_name, self.first_name)


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug_name = models.CharField(max_length=255, unique=True)
    short_desc = models.TextField(null=False, blank=False)
    desc = models.TextField(null=False, blank=False)
    is_public = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=False, blank=False)
    deadline = models.DateTimeField(null=False, blank=False)

    tags = models.ManyToManyField('kickstart.Tag', related_name='projects')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        create_benefit = not self.pk
        self.slug_name = slugify(u"{0}-{1}".format(self.name, self.user.username))

        super(Project, self).save(*args, **kwargs)

        if create_benefit:
            benefit = Benefit(project=self, amount='100.00', text=_(u"Get test example"))
            benefit.save()
            self.benefits.add(benefit)


class Benefit(models.Model):
    project = models.ForeignKey(Project, related_name='benefits')
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)
    text = models.TextField(null=False, blank=False)

    class Meta:
        ordering = ['amount']


class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
