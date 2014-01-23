import os
from django.db import models
from django.contrib.auth.models import User
from pytils.translit import slugify
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer
from django.core.mail import send_mail
import datetime
from mptt.models import MPTTModel, TreeForeignKey
from django.db import connection


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

    def close_recently_finished(self):
        now = timezone.now()
        base_queryset = (self.annotate(collected=models.Sum('projectdonation__benefit__amount'))
                             .filter(is_public=True, status=Project.IN_PROGRESS, deadline__lte=now))

        succeeded = base_queryset.filter(amount__lte=models.F('collected'))
        failed = (base_queryset.filter(models.Q(amount__gt=models.F('collected')) | models.Q(collected=None))
                               .select_related('user')
                               .prefetch_related(
                                    'projectdonation_set',
                                    'projectdonation_set__benefit',
                                    'projectdonation_set__user',
                                    'projectdonation_set__user__profile'))


        notify_succeeded = [(project.user.email, project.name) for project in succeeded]

        balances = {}
        notify_failed = []

        for project in failed:
            notify_failed.append((project.user.email, project.name))

            for donation in project.projectdonation_set.all():
                print 'return {0} to {1}'.format(donation.benefit.amount, donation.user.username)
                profile_id = donation.user.profile.pk

                if profile_id not in balances:
                    balances[profile_id] = donation.user.profile.balance

                balances[profile_id] += donation.benefit.amount


        update_param_list = [(balance, profile_id) for (profile_id, balance) in balances.items()]
        cursor = connection.cursor()
        cursor.executemany("UPDATE kickstart_profile SET balance=%s WHERE id=%s", update_param_list)

        succeeded.update(status=Project.SUCCESS)
        failed.update(status=Project.FAIL)

        for email, project_name in notify_succeeded:
            send_mail(
                _(u'Project funding is finished').encode('utf-8'),
                _(u'Congratulations! Your project "{0}" funding successfully finished!').format(project_name).encode('utf-8'),
                settings.DEFAULT_FROM_EMAIL,
                (email, )
            )

        for email, project_name in notify_failed:
            send_mail(
                _(u'Project funding is finished').encode('utf-8'),
                _(u'Sorry, but your project "{0}" funding has failed').format(project_name).encode('utf-8'),
                settings.DEFAULT_FROM_EMAIL,
                (email, )
            )


class Project(models.Model):
    IN_PROGRESS = 0
    SUCCESS = 1
    FAIL = 2
    STATUSES = (
        (IN_PROGRESS, _(u"In progress")),
        (SUCCESS, _(u"Success")),
        (FAIL, _(u"Fail"))
    )

    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    status = models.PositiveSmallIntegerField(default=0, choices=STATUSES, null=False, blank=False)
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


def tz_aware_now():
    """Current time with respect to the timezone."""
    return timezone.make_aware(datetime.datetime.now(),
                               timezone.get_default_timezone())


class Comment(MPTTModel):
    project = models.ForeignKey(Project, related_name='comments')
    user = models.ForeignKey(User)
    comment = models.TextField()
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    timestamp = models.DateTimeField(default=tz_aware_now)

    class MPTTMeta:
        order_insertion_by = ['timestamp']

    def __unicode__(self):
        result = self.user.username + ': ' + self.comment[:70]
        return result
