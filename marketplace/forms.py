from django import forms
from .models import Job, Proposal

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["title", "description", "budget_min", "budget_max"]

        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "Enter job title"
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Describe the job clearly"
            }),
            "budget_min": forms.NumberInput(attrs={
                "min": 0
            }),
            "budget_max": forms.NumberInput(attrs={
                "min": 0
            }),
        }


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ["bid_amount", "cover_letter"]

        widgets = {
            "bid_amount": forms.NumberInput(attrs={
                "placeholder": "Enter your bid in ₹",
            }),
            "cover_letter": forms.Textarea(attrs={
                "placeholder": "Explain why you are a great fit for this project...",
            }),
        }

        labels = {
            "bid_amount": "Your Bid Amount (₹)",
            "cover_letter": "Cover Letter",
        }