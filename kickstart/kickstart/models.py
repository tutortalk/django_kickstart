import os
from django.db import models
from django.contrib.auth.models import User
from pytils.translit import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer


def profile_avatar_dir(instance):
    return str(instance.user_id)


def profile_avatar_upload(instance, filename):
    name, ext = os.path.splitext(os.path.basename(filename))

    return os.path.join(
        profile_avatar_dir(),
        'avatar' + ext
    )


class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    about = models.TextField(null=True, blank=True)
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    avatar = models.ImageField(upload_to=profile_avatar_upload, null=True, blank=True)

    def __unicode__(self):
        return u"{0} - {1} - {2}".format(self.user.username, self.last_name, self.first_name)

    def get_avatar(self):
        if self.avatar:
            return get_thumbnailer(self.avatar)['avatar'].url

        else:
            return settings.STATIC_URL + "default_avatar.png"

    def clear_avatar(self):
        if self.avatar:
            folder = os.path.join(settings.MEDIA_ROOT, profile_avatar_dir(self))

            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception, e:
                    print e

            self.avatar.delete()
            self.save()


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


def project_file_dir(instance):
    project = instance.project

    return os.path.join(
        str(project.user_id),
        'project_{0}_files'.format(str(project.pk))
    )


def project_file_upload(instance, filename):
    name, ext = os.path.splitext(os.path.basename(filename))

    return os.path.join(
        project_file_dir(instance),
        'file' + ext
    )


class ProjectFile(models.Model):
    project = models.ForeignKey('kickstart.Project', related_name='files')
    original_filename = models.CharField(max_length=255, null=False, blank=False)
    file = models.FileField(upload_to=project_file_dir, null=False, blank=False)
    ext = models.CharField(max_length=10, null=False, blank=False)

    def __unicode__(self):
        return u"{0} - {1}".format(self.project.name, self.file.name)

    def delete(self, *args, **kwargs):
        self.file.delete()
        super(ProjectFile, self).delete(*args, **kwargs)


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
