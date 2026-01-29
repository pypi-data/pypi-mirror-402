# -*- coding: utf-8 -*-
from django.urls import path

from .views import SiteMapView


urlpatterns = [
    path(
        '<str:file_name>/',
        SiteMapView.as_view()
    )
]
