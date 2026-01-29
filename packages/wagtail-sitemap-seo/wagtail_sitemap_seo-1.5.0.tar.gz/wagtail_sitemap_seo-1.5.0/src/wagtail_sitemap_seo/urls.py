from django.urls import re_path
from .views import SitemapProxyView

urlpatterns = [
    re_path(r"^(?P<file_name>[-\w]+)\.xml$", SitemapProxyView.as_view(), name="sitemap_proxy"),
]
