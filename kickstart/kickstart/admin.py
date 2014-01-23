from django.contrib import admin
from kickstart.models import Profile, Project, ProjectDonation, Comment

admin.site.register(Profile)
admin.site.register(Comment)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'amount', 'deadline', 'is_public')
    search_fields = ('name', 'desc')
    list_filter = ('tags', )

class ProjectDonationAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'benefit')
    list_filter = ('project', )

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectDonation, ProjectDonationAdmin)
