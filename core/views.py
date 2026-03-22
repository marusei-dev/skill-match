import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from dotenv import load_dotenv
from .models import JobMatch, UserProfile

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)


def extract_text_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator=' ', strip=True)
        return text[:10000]
    except Exception as e:
        return f"Could not read the contents at the provided link: {str(e)}"


def generate_cv_with_gemini(profile, job_description):
    model = genai.GenerativeModel('gemini-2.5-flash')

    user_info = f"""
    Base Skills/Experience: {profile.base_skills}
    Phone Numbers: {profile.phone_numbers}
    LinkedIn: {profile.linkedin_url}
    GitHub: {profile.github_url}
    Other Websites: {profile.other_websites}
    """

    prompt = f"""
    You are an expert ATS-friendly CV writer.
    I will provide a User's Profile data and a Job Description.
    Your task is to match the user's experience with the job requirements and
    generate a highly tailored CV, however, you should not come up with too
    unrealistic experience that is too different from the user's.

    User Profile:
    {user_info}

    Job Description:
    {job_description}

    CRITICAL INSTRUCTION: You must output the CV scrictly in the following format.
    Do not add any introductory or concluding conversational text.
    Just output the CV content.

    SUMMARY
    [Write a compelling 2-3 sentence summary tailored to the job, highlighting
    key metrics if available]

    WORK EXPERIENCE
    [Heavily rely on the experience provided by the user, only changing it if it
    could be realistic, do not diverge too far from the user's experience]

    PROJECTS
    [Heavily rely on the projects already provided by the user. Change information
    only if it is very realistic and close to what the user did.]

    SKILLS
    [Here feel free to add relevant experience from the user's (priority) and
    then add up what the job description requires.]

    LANGUAGES
    [Copy from the user, if available]
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"There was an error during CV generation: {str(e)}"


def home(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.POST.get('action') == 'new_match':
            job_url = request.POST.get('job_url')
            job_text = request.POST.get('job_text')

            final_job_description = ""
            if job_text.strip():
                final_job_description = job_text
            elif job_url.strip():
                final_job_description = extract_text_from_url(job_url)

            profile, created = UserProfile.objects.get_or_create(user=request.user)

            generated_cv = generate_cv_with_gemini(profile, final_job_description)

            title_url = job_url if job_url else "Manual Text Input"
            JobMatch.objects.create(
                user=request.user,
                job_url=title_url,
                final_cv_text=generated_cv,
                added_skills="AI Analyzed"
            )

            return redirect('home')

        matches = JobMatch.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'index.html', {'matches': matches})

    return render(request, 'index.html')


@login_required(login_url='login')
def profile(request):
    profile_obj, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        phones = request.POST.getlist('phones[]')
        linkedin = request.POST.get('linkedin', '')
        github = request.POST.get('github', '')
        websites = request.POST.getlist('websites[]')
        base_skills = request.POST.get('base_skills', '')

        clean_phones = [p for p in phones if p.strip()]
        clean_websites = [w for w in websites if w.strip()]

        profile_obj.phone_numbers = clean_phones
        profile_obj.linkedin_url = linkedin
        profile_obj.github_url = github
        profile_obj.other_websites = clean_websites
        profile_obj.base_skills = base_skills
        profile_obj.save()

        return redirect('profile')

    return render(request, 'profile.html', {'profile': profile_obj})


def logout_user(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})
