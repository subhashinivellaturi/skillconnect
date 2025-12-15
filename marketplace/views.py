from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from .models import User
from django.contrib.auth.decorators import login_required
from .models import Job, Proposal, FreelancerProfile
from django.contrib import messages
from .forms import JobForm, ProposalForm
from datetime import timedelta
from django.utils import timezone

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse


from django.http import JsonResponse

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
#test
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from .models import Profile

def landing_page(request):
    return render(request, 'marketplace/landing_page.html')

def home(request):
    return render(request, 'marketplace/home.html')

def recruiter_auth(request):
    return render(request, 'marketplace/recruiter.html')

def freelancer_auth(request):
    return render(request, 'marketplace/freelancer.html')

def recruiter_signup(request):
    if request.method == "POST":
        company = request.POST.get("company_name")
        name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=email).exists():
            return render(request, "marketplace/recruiter.html", {
                "error": "Email already registered!",
            })

        user = User.objects.create(
            username=email,
            first_name=name,
            email=email,
            password=make_password(password),
            role="client"
        )
        user.save()

        login(request, user)
        return redirect("job_create")  # recruiter dashboard

    return redirect("recruiter_auth")




def recruiter_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None and user.role == "client":
            login(request, user)
            return redirect("recruiter_dashboard")
        else:
            return render(request, "marketplace/recruiter.html", {
                "login_error": "Invalid credentials!"
            })

    return redirect("recruiter_auth")


def freelancer_signup(request):
    if request.method == "POST":
        name = request.POST.get("full_name")
        skill = request.POST.get("primary_skill")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=email).exists():
            return render(request, "marketplace/freelancer.html", {
                "error": "Email already registered!",
            })

        user = User.objects.create(
            username=email,
            first_name=name,
            email=email,
            password=make_password(password),
            role="freelancer"
        )
        user.save()

        login(request, user)
        return redirect("job_list")  # freelancer dashboard

    return redirect("freelancer_auth")



def freelancer_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None and user.role == "freelancer":
            login(request, user)
            return redirect("freelancer_dashboard")
        else:
            return render(request, "marketplace/freelancer.html", {
                "login_error": "Invalid credentials!"
            })

    return redirect("freelancer_auth")







@login_required
def recruiter_dashboard(request):
    # base querysets (no slicing)
    jobs_qs = Job.objects.filter(client=request.user).order_by('-created_at')
    proposals_qs = Proposal.objects.filter(job__client=request.user).order_by('-created_at')

    context = {
        "active_jobs": Job.objects.filter(client=request.user, status="open").count(),
        "total_proposals": proposals_qs.count(),
        "hired_freelancers": proposals_qs.filter(status="accepted").count(),
        "jobs_this_week": jobs_qs.count(),          # you can later add date filter
        "unread_proposals": proposals_qs.filter(status="pending").count(),
        "hires_this_month": proposals_qs.filter(status="accepted").count(),
        "pending_verifications": 0,                 # if you add this later
        "recent_jobs": jobs_qs[:5],                 # slicing is OK here
        "recent_proposals": proposals_qs[:6],       # and here
    }

    return render(request, "marketplace/recruiter_dashboard.html", context)







@login_required
def freelancer_dashboard(request):
    user = request.user

    # Base queryset (NO slicing here)
    proposals_qs = Proposal.objects.filter(freelancer=user).order_by('-created_at')

    # Now you can safely filter
    jobs_won_qs = proposals_qs.filter(status="accepted")
    active_contracts = jobs_won_qs.filter(job__status="in_progress")

    # Slicing is only used for FINAL display, not calculations
    recent_proposals = proposals_qs[:8]

    # Recommended jobs
    recommended_jobs = Job.objects.filter(status="open").order_by("-created_at")[:6]

    # Primary skill
    primary_skill = ""
    try:
        profile = FreelancerProfile.objects.get(user=user)
        primary_skill = ", ".join([s.name for s in profile.skills.all()]) or ""
    except FreelancerProfile.DoesNotExist:
        pass

    total_proposals = proposals_qs.count()

    context = {
        "user": user,
        "primary_skill": primary_skill or "Freelancer",

        # Stats
        "active_proposals": proposals_qs.filter(status="pending").count(),
        "open_jobs_near_skill": recommended_jobs.count(),
        "total_proposals": total_proposals,
        "proposals_this_week": proposals_qs.count(),
        "jobs_won": jobs_won_qs.count(),

        "success_rate": round(
            (jobs_won_qs.count() / max(1, total_proposals)) * 100, 1
        ),

        "active_contracts": active_contracts.count(),
        "contracts_ending_soon": 0,
        "estimated_earnings": 0,

        # Display data
        "recommended_jobs": recommended_jobs,
        "recent_proposals": recent_proposals,
    }

    return render(request, "marketplace/freelancer_dashboard.html", context)



@login_required
def job_create(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            job.save()

            # ✅ SUCCESS MESSAGE
            messages.success(request, "🎉 Job posted successfully!")

            return redirect("job_list")
    else:
        form = JobForm()

    return render(request, "marketplace/job_create.html", {"form": form})




@login_required
def job_list(request):
    user = request.user

    if getattr(user, "role", None) == "client":
        # Recruiter: show only their jobs
        jobs = Job.objects.filter(client=user).order_by("-created_at")
    else:
        # Freelancer: show all open jobs
        jobs = Job.objects.filter(status="open").order_by("-created_at")

    return render(request, "marketplace/job_list.html", {"jobs": jobs})









@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)

    proposal_form = None
    # Only freelancers can apply
    if getattr(request.user, "role", None) == "freelancer" and request.user != job.client:
        if request.method == "POST":
            form = ProposalForm(request.POST)
            if form.is_valid():
                proposal = form.save(commit=False)
                proposal.job = job
                proposal.freelancer = request.user
                proposal.save()
                messages.success(request, "Your proposal has been submitted! 🎉")
                return redirect("job_detail", pk=job.pk)
            else:
                proposal_form = form
        else:
            proposal_form = ProposalForm()
    # Recruiter or others
    context = {
        "job": job,
        "proposal_form": proposal_form,
    }
    return render(request, "marketplace/job_detail.html", context)




@login_required
def proposal_create(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    # Only freelancers (and not the client) can apply
    if getattr(request.user, "role", None) != "freelancer" or request.user == job.client:
        messages.error(request, "You are not allowed to submit a proposal for this job.")
        return redirect("job_detail", pk=job.pk)

    if job.status != "open":
        messages.error(request, "This job is not accepting new proposals.")
        return redirect("job_detail", pk=job.pk)

    if request.method == "POST":
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.job = job
            proposal.freelancer = request.user
            proposal.status = "pending"
            proposal.save()

            messages.success(request, "Your proposal has been submitted successfully! 🎉")
            return redirect("job_detail", pk=job.pk)
        else:
            # Re-render job_detail with errors in the form
            return render(request, "marketplace/job_detail.html", {
                "job": job,
                "proposal_form": form,
            })

    # If someone opens this URL via GET, redirect back
    return redirect("job_detail", pk=job.pk)





@login_required
def proposal_accept(request, proposal_id):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    job = proposal.job

    # only job owner (recruiter) can accept
    if getattr(request.user, "role", None) != "client" or request.user != job.client:
        messages.error(request, "You are not allowed to modify this proposal.")
        return redirect("job_detail", pk=job.pk)

    if request.method == "POST":
        proposal.status = "accepted"
        proposal.save()

        # (optional) mark job as in progress
        if job.status == "open":
            job.status = "in_progress"
            job.save()

        # ✅ send email to freelancer
        try:
            job_link = request.build_absolute_uri(
                reverse("job_detail", args=[job.pk])
            )

            subject = f"Your proposal was ACCEPTED for '{job.title}'"
            message = (
                f"Hi {proposal.freelancer.first_name or 'Freelancer'},\n\n"
                f"Good news! The client '{job.client.first_name}' has ACCEPTED "
                f"your proposal for the job:\n\n"
                f"    {job.title}\n\n"
                f"Bid amount: ₹{proposal.bid_amount}\n"
                f"Job link: {job_link}\n\n"
                f"You can now coordinate with the client on next steps.\n\n"
                f"– SkillConnect"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[proposal.freelancer.email],
                fail_silently=True,  # avoid crashing if email fails
            )
        except Exception:
            # You can log this if you want; we just ignore for now
            pass

        messages.success(request, "You have accepted this proposal ✅")
        return redirect("job_detail", pk=job.pk)

    return redirect("job_detail", pk=job.pk)


@login_required
def proposal_reject(request, proposal_id):
    proposal = get_object_or_404(Proposal, pk=proposal_id)
    job = proposal.job

    # only job owner (recruiter) can reject
    if getattr(request.user, "role", None) != "client" or request.user != job.client:
        messages.error(request, "You are not allowed to modify this proposal.")
        return redirect("job_detail", pk=job.pk)

    if request.method == "POST":
        proposal.status = "rejected"
        proposal.save()

        # ✅ send email to freelancer
        try:
            job_link = request.build_absolute_uri(
                reverse("job_detail", args=[job.pk])
            )

            subject = f"Your proposal was REJECTED for '{job.title}'"
            message = (
                f"Hi {proposal.freelancer.first_name or 'Freelancer'},\n\n"
                f"The client '{job.client.first_name}' has REJECTED "
                f"your proposal for the job:\n\n"
                f"    {job.title}\n\n"
                f"Bid amount: ₹{proposal.bid_amount}\n"
                f"Job link: {job_link}\n\n"
                f"Don't be discouraged – you can keep applying to other jobs "
                f"on SkillConnect.\n\n"
                f"– SkillConnect"
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[proposal.freelancer.email],
                fail_silently=True,
            )
        except Exception:
            pass

        messages.success(request, "You have rejected this proposal ❌")
        return redirect("job_detail", pk=job.pk)

    return redirect("job_detail", pk=job.pk)







#landing page statics
def api_stats(request):
    return JsonResponse({
        "total_jobs": Job.objects.count(),
        "total_users": User.objects.count(),
        "total_proposals": Proposal.objects.count(),
        "active_now":  (User.objects.filter(is_active=True).count()),  # example
        "server_time": timezone.now().isoformat(),
    })



#recruiter profile
@login_required
def recruiter_profile(request, pk=None):
    recruiter = request.user  # logged-in recruiter

    # if pk is provided (public profile view)
    if pk:
        recruiter = get_object_or_404(User, pk=pk)

    # Fetch data for profile page
    posted_jobs = Job.objects.filter(client=recruiter).order_by("-created_at")
    recent_activity = []   # Fill with your activity model if you have one

    context = {
        "recruiter": recruiter,
        "posted_jobs": posted_jobs,
        "recent_activity": recent_activity,
    }
    return render(request, "marketplace/recruiter_profile.html", context)




@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)

    # Only owner (recruiter) can edit
    if request.user != job.client:
        messages.error(request, "You are not allowed to edit this job.")
        return redirect("job_detail", pk=job.pk)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect("job_detail", pk=job.pk)
    else:
        form = JobForm(instance=job)

    return render(request, "marketplace/job_edit.html", {"form": form, "job": job})


@login_required
def recruiter_profile_edit(request, pk):
    recruiter = get_object_or_404(User, pk=pk)

    if request.user != recruiter:
        messages.error(request, "Not allowed")
        return redirect("recruiter_profile", pk=pk)

    # ✅ SAFE: creates profile if missing
    profile, created = Profile.objects.get_or_create(user=recruiter)

    if request.method == "POST":
        profile.bio = request.POST.get("bio", "")
        profile.company = request.POST.get("company", "")
        profile.city = request.POST.get("profile_city", "")

        image = request.FILES.get("profile_image")

        if image:
            # Image validation
            if image.size > 2 * 1024 * 1024:
                messages.error(request, "Image must be under 2MB")
                return redirect("recruiter_profile_edit", pk=pk)

            if not image.content_type.startswith("image/"):
                messages.error(request, "Invalid image type")
                return redirect("recruiter_profile_edit", pk=pk)

            profile.profile_image = image

        profile.save()
        messages.success(request, "Profile updated successfully")
        return redirect("recruiter_profile", pk=pk)

    return render(request, "recruiter/profile_edit.html", {
        "profile": profile
    })



#test

def validate_profile_image(image):
    # 1️⃣ File size (2 MB limit)
    max_size = 2 * 1024 * 1024  # 2 MB
    if image.size > max_size:
        raise ValidationError("Image size should be less than 2 MB.")

    # 2️⃣ File extension check
    valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
    ext = image.name.split('.')[-1].lower()
    if ext not in valid_extensions:
        raise ValidationError("Only JPG, JPEG, PNG, or WEBP images are allowed.")

    # 3️⃣ Ensure it is a real image
    try:
        get_image_dimensions(image)
    except Exception:
        raise ValidationError("Uploaded file is not a valid image.")
    


#freelancer profile
@login_required
def freelancer_profile(request, pk):
    freelancer = get_object_or_404(User, pk=pk)

    tech_stack_list = []
    if hasattr(freelancer, "profile") and freelancer.profile.tech_stack:
        tech_stack_list = [
            t.strip() for t in freelancer.profile.tech_stack.split(",")
        ]


    skills_list = []
    if hasattr(freelancer, "profile") and freelancer.profile.skills:
        skills_list = [
            s.strip() for s in freelancer.profile.skills.split(",")
        ]    

    return render(request,"marketplace/freelancer_profile.html", {
        "freelancer": freelancer, "tech_stack_list": tech_stack_list, "skills_list": skills_list,
    })











