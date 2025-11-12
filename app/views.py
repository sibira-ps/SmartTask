from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import Task, UserProfile, ContactMessage
from .forms import ContactForm, TaskForm
from datetime import datetime, timedelta
import random
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

# =============================
# Home Page (Contact Form + Show Messages)
# =============================
def home(request):
    form = ContactForm()
    messages_list = ContactMessage.objects.order_by('-created_at')[:5]

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

    return render(request, 'app/index.html', {
        'form': form,
        'messages_list': messages_list,
    })

# =============================
# Signup Page
# =============================
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

# =============================
# Login Page
# =============================
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

# =============================
# Logout
# =============================
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

# =============================
# Dashboard View
# =============================
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

# =============================
# Task List View
# =============================
@login_required(login_url='login')
def task_list_view(request):
    tasks = Task.objects.filter(user=request.user, is_completed=False).order_by('due_date')
    return render(request, 'app/task-list.html', {'tasks': tasks})

# =============================
# Add Task View
# =============================
@login_required(login_url='login')
def add_task_view(request):
    if request.method == 'POST':
        title = request.POST.get('task')
        category = request.POST.get('category')
        project = request.POST.get('project')
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
                project=project,
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

# =============================
# Edit Task View
# =============================
@login_required(login_url='login')
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('task-list')
    else:
        form = TaskForm(instance=task)

    return render(request, 'app/edit_task.html', {'form': form, 'task': task})

# =============================
# Completed Tasks View
# =============================
@login_required(login_url='login')
def completed_tasks_view(request):
    tasks = Task.objects.filter(user=request.user, is_completed=True).order_by('-completed_date')
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)

    today_count = tasks.filter(completed_date__date=today).count()
    week_count = tasks.filter(completed_date__date__gte=week_ago).count()

    return render(request, 'app/completed-tasks.html', {
        'tasks': tasks,
        'stats': {
            'today': today_count,
            'week': week_count,
        }
    })

# =============================
# Forgot Password Flow (OTP)
# =============================
def forgot_password(request):
    if not request.session.get("step"):
        request.session["step"] = "email"

    step = request.session.get("step")
    return render(request, 'app/forgotpassword.html', {"step": step})

def verify_email(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session["email"] = email
            request.session["otp"] = otp
            request.session["step"] = "otp"

            send_mail(
                'Your SmartTask OTP Code',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "OTP has been sent to your email.")
        except User.DoesNotExist:
            messages.error(request, "No user with that email was found.")
    return redirect('forgotpassword')

def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if entered_otp == session_otp:
            request.session["step"] = "password"
            messages.success(request, "OTP verified. You can now reset your password.")
        else:
            messages.error(request, "Incorrect OTP. Try again.")
    return redirect('forgotpassword')

def reset_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        email = request.session.get("email")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('forgotpassword')

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            request.session.flush()
            messages.success(request, "Password reset successful. Please log in.")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('forgotpassword')

# =============================
# Projects View
# =============================
@login_required(login_url='login')
def projects_view(request):
    user = request.user
    tasks = Task.objects.filter(user=user, is_completed=False)

    category_data = {}
    for task in tasks:
        category = task.category or 'Uncategorized'

        if category not in category_data:
            category_data[category] = []

        category_data[category].append(task)

    return render(request, 'app/projects.html', {
        'category_data': category_data,
    })

# =============================
# Toggle Task Completion
# =============================
@login_required(login_url='login')
def toggle_task_completion(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        is_completed = 'is_completed' in request.POST
        task.is_completed = is_completed
        task.completed_date = timezone.now() if is_completed else None
        task.save()
    next_url = request.META.get('HTTP_REFERER', reverse('task-list'))
    return redirect(next_url)

# =============================
# Restore Task
# =============================
@login_required(login_url='login')
def restore_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user, is_completed=True)
    task.is_completed = False
    task.completed_date = None
    task.save()
    messages.success(request, f'Task "{task.title}" has been restored.')
    return redirect('completed-tasks')

# =============================
# Delete Task
# =============================
@require_POST
@login_required(login_url='login')
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id, user=request.user)
        task.delete()
        messages.success(request, f'Task "{task.title}" deleted successfully.')
    except Task.DoesNotExist:
        messages.error(request, "Task not found or already deleted.")
    return redirect('task-list')

# =============================
# Profile View
# =============================
@login_required
def profile_view(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        default_category = request.POST.get('default_category')
        email_notifications = request.POST.get('email_notifications') == 'on'

        user.first_name = full_name
        user.email = email
        user.save()

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
