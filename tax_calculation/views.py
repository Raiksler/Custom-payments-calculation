import requests
from django.shortcuts import render
import re
from tax_calculation.models import CustomTariff



class Ett_handler:
    def __init__(self, request):
        self.code = request.POST.get('code')
        self.specific_metric = request.POST.get('specific_metric')
        self.specific_label = request.POST.get('specific_label')
        self.valute = request.POST.get('valute')
        self.cource = request.POST.get('cource')
        self.usertype_cource = request.POST.get('usertype_cource')
        self.price = request.POST.get('price')
        self.tax = CustomTariff.objects.get(tnved_code=self.code).tax

    def get_parameters(self):  # Возврат контекста для шаблонов.
        return {'code' : self.code, 'specific_metric' : self.specific_metric, 'specific_label' : self.specific_label, 'valute' : self.valute,'price' : self.price, 'tax' : self.tax, 'cource' : self.cource, 'usertype_cource' : self.usertype_cource}

    def tax_type_checker(self):
        if (len(self.tax) <= 4 and self.tax[-1] == "%") or self.tax == "0":
            self.tax_type = 'advalore'
        elif len(self.tax.split()) == 1 and '+' not in self.tax:
            self.tax_type = 'specific'
        else:
            self.tax_type = 'combine'
        return self.tax_type

    def get_label(self): # Получение единицы измерения из специфической ставки.
        return re.search(r'(?<=\/).*', self.tax).group(0)
    
    def get_specific_tax(self): # Получение количественных данных из специфической ставки.
        return re.search(r'.{1,}\d', self.tax).group(0)

    def get_advalore_from_combine(self): # Получение адвалорной ставки из комбинированной.
        return re.search(r'.{1,}(?=%)', self.tax).group(0)

    def get_specific_from_combine(self): # Получение специфической ставки из комбинированной.
        return re.search(r'((?<= )|(?<=\+))\d{1,}.\d{1,}|(?<= )\d{1,}', self.tax).group(0)

    def get_combine_type(self): # Получение типа комбинированной ставки. Первый тип, содержит структуру "Но не менее", второй тип "% +"
        if '+' in self.tax:
            return 2
        else:
            return 1

    def get_valute(self): # Получение типа валюты из специфической ставки.
        if 'евро' in self.tax:
            return 'евро'
        else:
            return 'долл'

    def get_cource(self, valute): # Получение текущего курса валюты.
        if valute == 'долл':
            cource = requests.get('https://api.coingate.com/v2/rates/merchant/USD/RUB').json()
            return cource
        if valute == 'евро':
            cource = requests.get('https://api.coingate.com/v2/rates/merchant/EUR/RUB').json()
            return cource

    def calculate_tax(self, specific_metric=None, combine_type=None): # Непосредственный рассчет таможенной пошлины, в зависимости от ее типа.
        tax_type = self.tax_type_checker()
        if tax_type == 'advalore':
            if self.tax != '0':
                tax = float(self.price) * (float(self.tax[:-1]) / 100)
                return round(tax, 2)
            else:
                return 0
        elif tax_type == 'specific':
            if self.usertype_cource == '':  # Если не введен кастомный курс валюты
                specific_tax = self.get_specific_tax()
                tax = float(specific_tax) * float(specific_metric) * float(self.cource)
            else:
                specific_tax = self.get_specific_tax()
                tax = float(specific_tax) * float(specific_metric) * float(self.usertype_cource)
            return round(tax, 2)
        elif tax_type == 'combine':
            advalore_tax = self.get_advalore_from_combine()
            advalore_result = float(advalore_tax) / 100 * float(self.price)

            specific_tax = self.get_specific_from_combine()
            if self.usertype_cource == '':
                specific_result = float(specific_tax) * float(specific_metric) * float(self.cource)
            else:
                specific_result = float(specific_tax) * float(specific_metric) * float(self.usertype_cource)
            if combine_type == 1:
                if advalore_result > specific_result:
                    return {'result' : round(advalore_result, 2), 'formula_type' : 'advalore'}
                else:
                    return {'result' : round(specific_result, 2), 'formula_type' : 'specific'}
            elif combine_type == 2:
                return {'result' : round(advalore_result + specific_result, 2), 'formula_type' : 'summary'}



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
            parameters['specific_label'] = handler.get_label()
            parameters['valute'] = handler.get_valute()
            parameters['cource'] = handler.get_cource(valute=parameters['valute'])
            return render(request, 'result.html', context=parameters)
        else:
            calculated_tax = handler.calculate_tax(parameters['specific_metric'])
            parameters['calculated_tax'] = calculated_tax
            return render(request, 'result.html', context=parameters)
    #Проверка на достаточность данных для рассчета по комбинированной формуле. Если данных недостаточно, запрашиваем дополнительные если достаточно, производим рассчет.
    elif tax_type == 'combine':
        combine_type = handler.get_combine_type()
        if parameters['specific_metric'] == '' or parameters['price'] == '':
            parameters['specific_label'] = handler.get_label()
            parameters['valute'] = handler.get_valute()
            parameters['cource'] = handler.get_cource(valute=parameters['valute'])
            parameters['combine_type'] = combine_type
            return render(request, 'result.html', context=parameters)
        else:
            calculated_tax = handler.calculate_tax(specific_metric=parameters['specific_metric'], combine_type=combine_type)
            parameters['calculated_tax'] = calculated_tax['result']
            parameters['combine_formula_type'] = calculated_tax['formula_type']
            return render(request, 'result.html', context=parameters)