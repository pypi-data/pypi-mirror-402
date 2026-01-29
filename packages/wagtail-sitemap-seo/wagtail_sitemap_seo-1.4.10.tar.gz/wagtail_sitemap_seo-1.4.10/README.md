## Install

pip install git+https://github.com/gerry132/wagtail-sitemap-seo.git

## Configure

Add to INSTALLED_APPS:
- wagtail_sitemap_seo

Set:
- SEO_MAP_URL=<url to your root csv>

## Run

python manage.py build_sitemaps --output-dir ./sitemaps
