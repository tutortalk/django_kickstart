import os
from django.db import models
from django.contrib.auth.models import User
from pytils.translit import slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer
from django.core.mail import send_mail


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


class ProjectManager(models.Manager):
    def get_all_projects(self):
        return self.filter(is_public=True).filter(deadline__gt=timezone.now()).order_by('deadline')

    def search_projects(self, search):
        tagged_project_ids = Tag.objects.filter(name__icontains=search).values_list('projects', flat=True)
        tagged_project_ids = list(set(tagged_project_ids))
        query = models.Q(name__icontains=search) | models.Q(pk__in=tagged_project_ids)

        return self.get_all_projects().filter(query)


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug_name = models.CharField(max_length=255, unique=True)
    short_desc = models.TextField(null=False, blank=False)
    desc = models.TextField(null=False, blank=False)
    is_public = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=False, blank=False)
    deadline = models.DateTimeField(null=False, blank=False)
    objects = ProjectManager()

    tags = models.ManyToManyField('kickstart.Tag', related_name='projects')
    donators = models.ManyToManyField(User, through='ProjectDonation', related_name='donations')

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

    def get_donations(self):
        return list(ProjectDonation.objects.filter(project=self).select_related('benefit').all())


class ProjectDonation(models.Model):
    project = models.ForeignKey('kickstart.Project')
    user = models.ForeignKey(User)
    benefit = models.ForeignKey('kickstart.Benefit')

    def __unicode__(self):
        return u"{0} - {1} - {2} bucks".format(self.project.name, self.user.username, self.benefit.amount)

    def save(self, *args, **kwargs):
        take_money = not self.pk
        super(ProjectDonation, self).save(*args, **kwargs)

        if take_money:
            self.user.profile.balance -= self.benefit.amount
            self.user.profile.save()

            notification_message = u'Congratulation! Your project received donation {amount} bucks from user {user}'.format(
                amount=self.benefit.amount,
                user=self.user.username
            )
            send_mail(
                _(u'Your project "{0}" received donation'.format(self.project.name)).encode('utf-8'),
                _(notification_message).encode('utf-8'),
                settings.DEFAULT_FROM_EMAIL,
                (self.user.email, )
            )

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

    def __unicode__(self):
        return str(self.amount)


class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name
