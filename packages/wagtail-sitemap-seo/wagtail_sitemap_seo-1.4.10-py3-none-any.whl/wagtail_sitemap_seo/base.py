import xml.etree.cElementTree as ET
from datetime import datetime


class BaseBuilder:

    def _format_date(self, date):
        if not date:
            return
        if isinstance(date, str):
            return datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%Y-%m-%d')

    def build_url_elem(self, url):
        url_elem = ET.Element('url')
        loc_elem = ET.Element('loc')
        publish_elem = ET.Element('lastmod')

        publish_elem.text = self._format_date(url.last_published_at)
        loc_elem.text = url.full_url
        url_elem.append(loc_elem)
        url_elem.append(publish_elem)

        for trans in url.get_translations():

            lang_elem = ET.Element('xhtml:link')
            lang_elem.attrib['rel'] = 'alternate'
            lang_elem.attrib['hreflang'] = trans.locale.language_code
            lang_elem.attrib['href'] = trans.full_url

            url_elem.append(lang_elem)
        lang_elem = ET.Element('xhtml:link')
        lang_elem.attrib['rel'] = 'alternate'
        lang_elem.attrib['hreflang'] = 'en'
        lang_elem.attrib['href'] = url.full_url
        url_elem.append(lang_elem)

        lang_elem_default = ET.Element('xhtml:link')
        lang_elem_default.attrib['rel'] = 'alternate'
        lang_elem_default.attrib['hreflang'] = 'x-default'
        lang_elem_default.attrib['href'] = url.full_url
        url_elem.append(lang_elem_default)
        return url_elem
