from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone_numbers = models.JSONField(default=list, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    other_websites = models.JSONField(default=list, blank=True, null=True)

    base_skills = models.TextField(
        blank=True,
        null=True,
        help_text="Your base skills and experience")

    def __str__(self):
        return f"{self.user.username}'s Profile"


class JobMatch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_url = models.URLField(help_text="URL of the job listing")

    final_cv_text = models.TextField(
        blank=True,
        null=True,
        help_text="The final CV text after processing")
    added_skills = models.TextField(
        blank=True,
        null=True,
        help_text="Skills added to the CV based on the job listing")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job Match for {self.user.username} - {self.job_url}"
