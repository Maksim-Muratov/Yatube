from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm
from django.shortcuts import render


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def password_reset_form(request):
    return render(request, 'users/password_reset_form.html')
