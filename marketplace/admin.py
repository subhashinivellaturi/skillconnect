from django.contrib import admin
from .models import User, Job, Proposal, FreelancerProfile, Skill

admin.site.register(User)
admin.site.register(Job)
admin.site.register(Proposal)
admin.site.register(FreelancerProfile)
admin.site.register(Skill)


# Register your models here.
