from django.shortcuts import render
import textwrap

from django.http import HttpResponse
from django.views.generic.base import View

class HomePageView(View):

    def dispatch(request, *args, **kwargs):
        response_text = textwrap.dedent('Django is Running!')
        return HttpResponse(response_text)
