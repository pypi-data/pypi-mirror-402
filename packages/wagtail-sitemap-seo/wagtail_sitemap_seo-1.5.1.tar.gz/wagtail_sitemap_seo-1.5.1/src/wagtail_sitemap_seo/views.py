from __future__ import annotations

from django.conf import settings
from django.http import FileResponse, Http404
from django.views import View
from django.core.files.storage import default_storage


class SitemapProxyView(View):
    """
    Serve sitemap XML from the configured storage backend (local in dev, S3 in UAT/prod),
    but under the uat.ireland.ie hostname.
    """

    def get(self, request, file_name: str):
        sitemap_dir = getattr(settings, "SITEMAP_DIR", "sitemap").strip("/")
        key = f"{sitemap_dir}/{file_name}.xml"

        if not default_storage.exists(key):
            raise Http404(f"Missing sitemap: {key}")

        f = default_storage.open(key, "rb")
        resp = FileResponse(f, content_type="application/xml")
        resp["Cache-Control"] = "public, max-age=300"
        return resp
