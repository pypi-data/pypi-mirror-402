from __future__ import annotations

from io import BytesIO
import xml.etree.cElementTree as ET
import csv
import urllib.request
from wagtail.models import Site

from wagtail.models import Page
from wagtail.models import Locale

from django.conf import settings

from .base import BaseBuilder
from .s3_helper import save_xml


site = Site.objects.get(is_default_site=True)


def email_management_enabled():
    return getattr(settings, "WAGTAIL_EMAIL_MANAGEMENT_ENABLED", True)


class RootBuilder(BaseBuilder):

    def __init__(self, root_file):
        self.root_file = root_file
        self.root_pages = []
        self.page_url_map = {}
        self.site = site.site_name


    def site_map_init(self, root=False):
        xml_root = ET.Element('urlset')
        xml_root.attrib['xmlns:xsi'] = "https://www.w3.org/2001/XMLSchema-instance"
        xml_root.attrib['xmlns:xhtml'] = "https://www.w3.org/1999/xhtml"
        xml_root.attrib['xsi:schemaLocation'] = "https://www.sitemaps.org/schemas/sitemap/0.9" \
                                                + " https://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
        xml_root.attrib['xmlns'] = "https://www.sitemaps.org/schemas/sitemap/0.9"

        return xml_root


    def add_xml_root(self, xml_root):
        sitemap_index = ET.Element('sitemapindex')
        sitemap_index.attrib['xmlns'] = 'http://www.sitemaps.org/schemas/sitemap/0.9'

        for url in self.root_pages:
            elem = self.build_root_elem(url)
            sitemap_index.append(elem)

        xml_root.append(sitemap_index)
        tree = ET.ElementTree(xml_root)

        if settings.SITEMAP_WRITE_S3:

            buffer = BytesIO()
            tree.write(buffer, encoding='utf-8', xml_declaration=True)
            content = buffer.getvalue()

            if settings.SITEMAP_DIR:
                save_xml('{}/root_map.xml'.format(settings.SITEMAP_DIR), content)
            else:
                save_xml('root_map.xml', content)
        else:
            tree.write('root_map.xml', encoding='utf-8', xml_declaration=True)

    def get_site(self):
        return self.site

    def _load_urls_from_root(self):
        print(settings.SEO_MAP_URL)
        urls = []
        if settings.SEO_MAP_URL:
            response = urllib.request.urlopen(settings.SEO_MAP_URL)

            lines = [line.decode('utf-8') for line in response.readlines()]
            cr = csv.reader(lines)

            for row in cr:
                urls.append(row[0])

            # TODO: perhaps add multisite support
            print(urls)
            for series in urls:
                print(urls)
                locale = Locale.objects.get(language_code='en')
                p = Page.objects.live().filter(slug=series.strip("/"), locale=locale)
                if len(p) > 1:
                    print('here')
                    for res in p:
                        print(res.get_url())
                        print('/en/' + series)
                        if res.get_url() == '/en/' + series:
                            self.page_url_map[series] = res
                            self.root_pages.append(res)
                else:
                    self.page_url_map[series] = p[0]
                    self.root_pages.append(p[0])
