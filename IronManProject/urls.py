"""IronManProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from KPI import views
from django.views import static 
from django.conf import settings 
from django.conf.urls import url 



urlpatterns = [
    path('json_test/', views.json_test),
    path('', views.relogin),
    path('login/', views.login),
    path('logininfo/', views.logininfo),
    path('rules/', views.rules),
    path('logout/', views.logout),
    path('viewinfo/', views.viewinfo),
    path('AddRules/', views.AddRules),
    path('EditRules/', views.EditRules),
    path('register/', views.register),
    path('managerkaohe/', views.managerkaohe),
    path('AddEvent/', views.AddEvent),
    path('Editevents/', views.Editevents),
    path('Edittarget/', views.Edittarget),
    path('Editstufftarget/', views.Editstufftarget),
    path('Edit/', views.Edit),
    path('Modrole/', views.ModRole),
    path('Modinfo/', views.Modinfo),
    path('InfoModed/', views.InfoModed),
    path('Manage/', views.Manage),
    path('admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT}, name='static'),    
]
