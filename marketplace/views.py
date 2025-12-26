from django.shortcuts import render, redirect, get_object_or_404 
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import User, Job, Proposal, Profile
from .forms import JobForm, ProposalForm
from django.core.mail import send_mail
from django.conf import settings


# --------------------
# LANDING / HOME
# --------------------
def landing_page(request):
    return render(request, "marketplace/landing_page.html")


def home(request):
    return render(request, "marketplace/home.html")


# --------------------
# AUTH PAGES
# --------------------
def recruiter_auth(request):
    return render(request, "marketplace/recruiter.html")


def freelancer_auth(request):
    return render(request, "marketplace/freelancer.html")


# --------------------
# LOGIN / SIGNUP
# --------------------
# --------------------
# LOGIN / SIGNUP
# --------------------
def recruiter_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user and user.role == "client":
            login(request, user)

            # Email on successful login
            if user.email:
                send_mail(
                    subject="Login notification",
                    message="You have successfully logged in to your account.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

            return redirect("recruiter_dashboard")

        messages.error(request, "Invalid credentials")

    # render the combined recruiter page
    return render(request, "marketplace/recruiter.html")


def recruiter_signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        signup_errors = []

        if password != confirm_password:
            signup_errors.append("Passwords do not match.")

        if User.objects.filter(username=email).exists():
            signup_errors.append("An account with this email already exists.")

        if signup_errors:
            return render(
                request,
                "marketplace/recruiter.html",
                {"signup_errors": signup_errors},
            )

        # create client user (recruiter)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
            role="client",
        )

        # Email on successful registration
        if user.email:
            send_mail(
                subject="Welcome to SkillConnect",
                message="Your recruiter account has been registered successfully.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        messages.success(request, "Recruiter registered successfully")
        return redirect("recruiter_auth")  # loads recruiter.html

    # GET fallback
    return render(request, "marketplace/recruiter.html")


def freelancer_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user and user.role == "freelancer":
            login(request, user)

            # Email on successful login
            if user.email:
                send_mail(
                    subject="Login notification",
                    message="You have successfully logged in to your account.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )

            return redirect("freelancer_dashboard")

        messages.error(request, "Invalid credentials")

    return render(request, "marketplace/freelancer.html")


def freelancer_signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        signup_errors = []

        if password != confirm_password:
            signup_errors.append("Passwords do not match.")

        if User.objects.filter(username=email).exists():
            signup_errors.append("An account with this email already exists.")

        if signup_errors:
            return render(
                request,
                "marketplace/freelancer.html",
                {"signup_errors": signup_errors},
            )

        # create freelancer user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
            role="freelancer",
        )

        # Email on successful registration
        if user.email:
            send_mail(
                subject="Welcome to SkillConnect",
                message="Your freelancer account has been registered successfully.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

        messages.success(request, "Freelancer registered successfully")
        return redirect("freelancer_auth")

    return render(request, "marketplace/freelancer.html")


# --------------------
# DASHBOARDS
# --------------------
@login_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(client=request.user)
    return render(request, "marketplace/recruiter_dashboard.html", {"jobs": jobs})


@login_required
def freelancer_dashboard(request):
    jobs = Job.objects.filter(status="open")
    return render(request, "marketplace/freelancer_dashboard.html", {"jobs": jobs})


# --------------------
# JOBS
# --------------------
@login_required
def job_create(request):
    form = JobForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.client = request.user
        job.save()
        return redirect("recruiter_dashboard")

    return render(request, "marketplace/job_create.html", {"form": form})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, client=request.user)
    form = JobForm(request.POST or None, instance=job)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("recruiter_dashboard")

    return render(request, "marketplace/job_edit.html", {"form": form})


def job_list(request):
    jobs = Job.objects.filter(status="open")
    return render(request, "marketplace/job_list.html", {"jobs": jobs})


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, "marketplace/job_detail.html", {"job": job})


# --------------------
# PROPOSALS
# --------------------
@login_required
def proposal_create(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    proposal = Proposal.objects.create(
        job=job,
        freelancer=request.user,
        cover_letter=request.POST.get("cover_letter")
    )

    # Email to freelancer
    if request.user.email:
        send_mail(
            subject="Application submitted",
            message="Your application for the job role is submitted. After review, we will update you.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )

    return redirect("job_list")


@login_required
def proposal_accept(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    proposal.status = "accepted"
    proposal.save()

    freelancer_email = proposal.freelancer.email
    if freelancer_email:
        send_mail(
            subject="Proposal status update",
            message="Your proposal for the applied role is accepted.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[freelancer_email],
            fail_silently=True,
        )

    return redirect("recruiter_dashboard")


@login_required
def proposal_reject(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    proposal.status = "rejected"
    proposal.save()

    freelancer_email = proposal.freelancer.email
    if freelancer_email:
        send_mail(
            subject="Proposal status update",
            message="Your proposal for the applied role is rejected.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[freelancer_email],
            fail_silently=True,
        )

    return redirect("recruiter_dashboard")





# --------------------
# API STATS
# --------------------
def api_stats(request):
    return JsonResponse({
        "jobs": Job.objects.count(),
        "clients": User.objects.filter(role="client").count(),
        "freelancers": User.objects.filter(role="freelancer").count(),
        "proposals": Proposal.objects.count(),
    })


# --------------------
# PROFILES
# --------------------
@login_required
def recruiter_profile(request, pk):
    user = get_object_or_404(User, pk=pk, role="client")
    return render(request, "marketplace/recruiter_profile.html", {"user": user})


@login_required
def recruiter_profile_edit(request, pk):
    profile = get_object_or_404(Profile, user_id=pk)

    if request.method == "POST":
        profile.bio = request.POST.get("bio")
        profile.city = request.POST.get("city")
        profile.company = request.POST.get("company")
        profile.save()
        return redirect("recruiter_profile", pk=pk)

    return render(request, "marketplace/recruiter_profile.html", {"profile": profile})


@login_required
def freelancer_profile(request, pk):
    user = get_object_or_404(User, pk=pk, role="freelancer")
    return render(request, "marketplace/freelancer_profile.html", {"user": user})
