# coding=utf-8
from __future__ import unicode_literals


"""foward_bot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from foward_bot.telegram_API.urls import urlpatterns as apiurlpatterns
from .views import FowarderView


urlpatterns = [
    # url(r'(?P<token>[-_:a-zA-Z0-9]+)/$', FowarderView.as_view(), name='webhook'),
    # url(r'^api/', include('foward_bot.telegram_API.urls', namespace='api')),
]