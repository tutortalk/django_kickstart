from django.core.management.base import BaseCommand
from kickstart.models import Project


class Command(BaseCommand):
    help = 'Check projects that reach deadlines'

    def handle(self, *args, **options):
        Project.objects.close_recently_finished()
