from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.utils.html import strip_tags

# Create your views here.
def dashboard_view(request):
    print(request.user)
    if request.user.is_anonymous:
        return redirect('/login')
    return render(request, 'index.html')

def loginUser(request):
    #if request.method == 'POST':
    #check if user exists and had entered correct password
    username = request.POST.get('username')
    password = request.POST.get('password')
    print(username, password)
    user = authenticate(username=username, password=password)
    if user is not None:
        # A backend authenticated the credentials
        login(request, user)
        return redirect("/")
    else:
        # No backend authenticated the credentials
        return render(request, 'login.html')
    #return render(request, 'login.html')

def logoutUser(request):
    logout(request)
    return redirect('/login')

def station_view(request):
    return render(request, 'station.html')

def user_view(request):
    return render(request, 'user.html')

def summary_view(request):
    return render(request, 'summary.html')

