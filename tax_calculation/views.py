import requests
from django.shortcuts import render
import re
from tax_calculation.models import CustomTariff

# Create your views here.

class Ett_handler:
    def __init__(self, request):
        self.code = request.POST.get('code')
        self.specific_metric = request.POST.get('specific_metric')
        self.specific_label = request.POST.get('specific_label')
        self.specific_valute = request.POST.get('specific_valute')
        self.cource = request.POST.get('cource')
        self.usertype_cource = request.POST.get('usertype_cource')
        self.price = request.POST.get('price')
        self.tax = CustomTariff.objects.get(tnved_code=self.code).tax

    def get_parameters(self):  # Возврат контекста для шаблонов.
        return {'code' : self.code, 'specific_metric' : self.specific_metric, 'specific_label' : self.specific_label, 'specific_valute' : self.specific_valute,'price' : self.price, 'tax' : self.tax, 'cource' : self.cource, 'usertype_cource' : self.usertype_cource}

    def tax_type_checker(self):
        if (len(self.tax) <= 3 and self.tax[-1] == "%") or self.tax == "0":
            self.tax_type = 'advalore'
        elif len(self.tax.split()) == 1:
            self.tax_type = 'specific'
        else:
            self.tax_type = 'combine'
        return self.tax_type

    def get_specific_label(self):
        return re.search(r'(?<=\/).*', self.tax).group(0)
    
    def get_specific_tax(self):
        return re.search(r'.{1,}\d', self.tax).group(0)

    def get_specific_valute(self):
        if 'евро' in self.tax:
            return 'евро'
        else:
            return 'долл'

    def get_cource(self, valute):
        if valute == 'долл':
            cource = requests.get('https://api.coingate.com/v2/rates/merchant/USD/RUB').json()
            return cource
        if valute == 'евро':
            cource = requests.get('https://api.coingate.com/v2/rates/merchant/EUR/RUB').json()
            return cource

    def calculate_tax(self, specific_metric=None):
        tax_type = self.tax_type_checker()
        if tax_type == 'advalore':
            if self.tax != '0':
                tax = int(self.price) * (int(self.tax[:-1]) / 100)
                return round(tax, 2)
            else:
                return 0
        elif tax_type == 'specific':
            if self.usertype_cource == '':  # Если не введен кастомный курс валюты
                specific_tax = self.get_specific_tax()
                tax = float(specific_tax) * int(specific_metric) * float(self.cource)
            else:
                specific_tax = self.get_specific_tax()
                tax = float(specific_tax) * int(specific_metric) * float(self.usertype_cource)
            return round(tax, 2)



def index(request):
    return render(request, 'index.html')

def calculate_tax(request):
    handler = Ett_handler(request)
    tax_type = handler.tax_type_checker()
    parameters = handler.get_parameters()
    parameters['tax_type'] = tax_type
    #Проверка на достаточность данных для рассчета по адвалорной формуле. Если данных недостаточно, запрашиваем дополнительные, если достаточно, производим рассчет.
    if tax_type == 'advalore':
        if parameters['price'] == '':
            return render(request, 'result.html', context=parameters)
        else:
            calculated_tax = handler.calculate_tax()
            parameters['calculated_tax'] = calculated_tax
            return render(request, 'result.html', context=parameters)
    #Проверка на достаточность данных для рассчета по специфической формуле. Если данных недостаточно, запрашиваем дополнительные если достаточно, производим рассчет.
    elif tax_type == 'specific':
        if parameters['specific_metric'] == '':
            parameters['specific_label'] = handler.get_specific_label()
            parameters['specific_valute'] = handler.get_specific_valute()
            parameters['cource'] = handler.get_cource(valute=parameters['specific_valute'])
            return render(request, 'result.html', context=parameters)
        else:
            calculated_tax = handler.calculate_tax(parameters['specific_metric'])
            parameters['calculated_tax'] = calculated_tax
            print(parameters)
            return render(request, 'result.html', context=parameters)
    #Проверка на достаточность данных для рассчета по комбинированной формуле. Если данных недостаточно, запрашиваем дополнительные если достаточно, производим рассчет.
    elif tax_type == 'combine':
        if parameters['mass'] == '' or parameters['price'] == '':
            return render(request, 'result.html', context=parameters)