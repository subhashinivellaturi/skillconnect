from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path('recruiter/', views.recruiter_auth, name='recruiter_auth'),
    path('freelancer/', views.freelancer_auth, name='freelancer_auth'),
    path('recruiter/login/', views.recruiter_login, name='recruiter_login'),
    path('recruiter/signup/', views.recruiter_signup, name='recruiter_signup'),
    path('freelancer/login/', views.freelancer_login, name='freelancer_login'),
    path('freelancer/signup/', views.freelancer_signup, name='freelancer_signup'),
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path("freelancer/dashboard/", views.freelancer_dashboard, name="freelancer_dashboard"),
    path('recruiter/jobs/create/', views.job_create, name='job_create'),
    path("freelancer/jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.proposal_create, name="proposal_create"),
    path("proposals/<int:proposal_id>/accept/", views.proposal_accept, name="proposal_accept"),
    path("proposals/<int:proposal_id>/reject/", views.proposal_reject, name="proposal_reject"),

    # urls.py
    path('api/stats/', views.api_stats, name='api_stats'),

    #recruiter profile
    path("recruiter/profile/<int:pk>/", views.recruiter_profile, name="recruiter_profile"),
    path("recruiter/profile/<int:pk>/edit/", views.recruiter_profile_edit, name="recruiter_profile_edit"),

    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),

    #job create
    path("jobs/create/", views.job_create, name="job_create"),

    #freelancer profile
    path("freelancer/<int:pk>/", views.freelancer_profile, name="freelancer_profile"),


]

