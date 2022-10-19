from django.shortcuts import render, HttpResponse
from tnved.models import CustomTariff

# Create your views here.

# Placeholder
def tnved_info(request):
    result = CustomTariff.objects.get(tnved_code='0202203001').name
    return HttpResponse(result)
