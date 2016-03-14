from django.conf.urls import url
from django.views.generic import TemplateView

import app.views as app_views


urlpatterns = [
    url(r'^(|/)$', app_views.HomeView.as_view()),
    url(r'^florida$', app_views.StateView.as_view(state='FL')),
    url(r'^faqs$', TemplateView.as_view(template_name='faqs.html')),
    ]