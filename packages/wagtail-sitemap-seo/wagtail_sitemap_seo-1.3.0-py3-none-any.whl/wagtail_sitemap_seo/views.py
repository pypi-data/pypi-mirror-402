from django.shortcuts import HttpResponse
from django.views import View


class SiteMapView(View):

    def get(self, request, file_name, content_type='application/xml'):
        return HttpResponse(open(file_name + ".xml").read(), content_type='text/xml')
