from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import ContactMessage, Task

# -----------------------------
# Signup Form
# -----------------------------
class SignupForm(forms.Form):
    fullName = forms.CharField(max_length=100, label='Full Name')
    email = forms.EmailField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)
    confirmPassword = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmPassword")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

# -----------------------------
# Login Form
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput)

# -----------------------------
# Contact Form
# -----------------------------
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your Email'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 4}),
        }

# -----------------------------
# Task Form (for Add/Edit Task)
# -----------------------------
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'category', 'start_date', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Task Title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Task Description'}),
            'category': forms.Select(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
