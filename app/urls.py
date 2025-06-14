from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('tasks/', views.task_list_view, name='task-list'),
    path('add-task/', views.add_task_view, name='add-task'),
    path('completed-tasks/', views.completed_tasks_view, name='completed-tasks'),
    path('forgotpassword/', views.forgot_password_view, name='forgotpassword'),
    path('projects/', views.projects_view, name='projects'),
    path('tasks/toggle-completion/<int:task_id>/', views.toggle_task_completion, name='toggle-task-completion'),
    path('restore-task/<int:task_id>/', views.restore_task, name='restore-task'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete-task'),
    path('profile/', views.profile_view, name='profile'),  # <-- added profile path
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='app/password_change.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='app/password_change_done.html'), name='password_change_done'),
]

