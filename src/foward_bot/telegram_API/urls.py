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
from rest_framework.routers import SimpleRouter
from .views import TelegramView, BotViewSet

app_name = "telegram_API"

urlpatterns = [
    url(r'^webhook/(?P<token>[-_:a-zA-Z0-9]+)', TelegramView.as_view(), name='webhook'),
    url(r'bots', BotViewSet, name='api'),
]

# router = SimpleRouter(trailing_slash=False)
#
# router.register(r'bots', BotViewSet, base_name='api')
#
# router.register(r'^(?P<token>[-_:a-zA-Z0-9]+)/$', TelegramView.as_view(), base_name='webhook_integration')
#
# urlpatterns += router.get_urls()