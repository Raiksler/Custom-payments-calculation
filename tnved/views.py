from django.shortcuts import render, HttpResponse
from tnved.models import CustomTariff

# Create your views here.


def tnved_tax(request):
    result = CustomTariff.objects.get(tnved_code='0202203001').tax
    return HttpResponse(result)
