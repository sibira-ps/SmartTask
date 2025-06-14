from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import Task
from datetime import datetime, timedelta
import random
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import UserProfile
# Home Page
def home(request):
    return render(request, 'app/index.html')


# Signup Page
def signup_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('fullName', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
            return redirect('signup')

        names = full_name.strip().split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''

        username = email
        user = User.objects.create_user(username=username, email=email, password=password,
                                        first_name=first_name, last_name=last_name)

        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('login')

    return render(request, 'app/signup.html')


# Login Page
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'app/login.html')


# Logout
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# Dashboard with stats and motivational quote
@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, is_completed=True).count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    quotes = [
        "Keep going, you're doing great!",
        "Every task completed is a step forward.",
        "Stay focused and keep pushing!",
        "Success is the sum of small efforts repeated daily.",
    ]
    motivational_quote = random.choice(quotes)

    return render(request, 'app/dashboard.html', {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress': int(progress),
        'motivational_quote': motivational_quote,
        'user_email': user.email,
        'user_name': user.first_name or user.username,
    })


# Task List (pending tasks)
@login_required(login_url='login')
def task_list_view(request):
    tasks = Task.objects.filter(user=request.user, is_completed=False).order_by('due_date')
    return render(request, 'app/task-list.html', {'tasks': tasks})


# Add Task — with due_date and start_date validation
@login_required(login_url='login')
def add_task_view(request):
    if request.method == 'POST':
        title = request.POST.get('task')
        category = request.POST.get('category')
        due_date_str = request.POST.get('due_date')
        start_date_str = request.POST.get('start_date')

        due_date = None
        start_date = None

        try:
            if due_date_str:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('add-task')

        if title and category and due_date and start_date:
            Task.objects.create(
                user=request.user,
                title=title,
                category=category,
                due_date=due_date,
                start_date=start_date,
                is_completed=False,
                completed_date=None
            )
            messages.success(request, 'Task added successfully!')
            return redirect('add-task')
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'app/add-task.html')


# Completed Tasks (for current user) with stats
@login_required(login_url='login')
def completed_tasks_view(request):
    tasks = Task.objects.filter(user=request.user, is_completed=True).order_by('-completed_date')

    today = timezone.localdate()
    week_ago = today - timedelta(days=7)

    today_count = tasks.filter(
        completed_date__isnull=False,
        completed_date__date=today
    ).count()

    week_count = tasks.filter(
        completed_date__isnull=False,
        completed_date__date__gte=week_ago
    ).count()

    return render(request, 'app/completed-tasks.html', {
        'tasks': tasks,
        'stats': {
            'today': today_count,
            'week': week_count,
        }
    })


# Forgot Password page
def forgot_password_view(request):
    return render(request, 'app/forgotpassword.html')


# Projects - list tasks by category
@login_required(login_url='login')
def projects_view(request):
    user = request.user
    work_tasks = Task.objects.filter(user=user, category='Work', is_completed=False)
    personal_tasks = Task.objects.filter(user=user, category='Personal', is_completed=False)
    health_tasks = Task.objects.filter(user=user, category='Health', is_completed=False)
    study_tasks = Task.objects.filter(user=user, category='Study', is_completed=False)

    return render(request, 'app/projects.html', {
        'work_tasks': work_tasks,
        'personal_tasks': personal_tasks,
        'health_tasks': health_tasks,
        'study_tasks': study_tasks,
    })


# Toggle Task Completion
@login_required(login_url='login')
def toggle_task_completion(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        is_completed = 'is_completed' in request.POST
        task.is_completed = is_completed
        if is_completed:
            task.completed_date = timezone.now()
        else:
            task.completed_date = None
        task.save()

    next_url = request.META.get('HTTP_REFERER', reverse('task-list'))
    return redirect(next_url)


# Restore Completed Task
@login_required(login_url='login')
def restore_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user, is_completed=True)
    task.is_completed = False
    task.completed_date = None
    task.save()
    messages.success(request, f'Task "{task.title}" has been restored.')
    return redirect('completed-tasks')


# Delete Task (POST only)
@require_POST
@login_required(login_url='login')
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
        messages.success(request, f'Task "{task.title}" deleted successfully.')
    except Task.DoesNotExist:
        messages.error(request, "Task not found or already deleted.")
    return redirect('completed-tasks')


# Restore Task (AJAX JSON version)
@require_POST
@login_required(login_url='login')
def restore_task_ajax(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user, is_completed=True)
    task.is_completed = False
    task.completed_date = None
    task.save()
    return JsonResponse({'success': True})


# ========================
# New: Profile View
# ========================
  # Assuming you have a UserProfile model to hold extra fields

@login_required
def profile_view(request):
    user = request.user
    # Get or create user profile for extra fields like default_category, email_notifications
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        default_category = request.POST.get('default_category')
        email_notifications = request.POST.get('email_notifications') == 'on'

        # Update user model
        user.first_name = full_name
        user.email = email
        user.save()

        # Update user profile
        user_profile.default_category = default_category
        user_profile.email_notifications = email_notifications
        user_profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'app/profile.html', context)
