from django.shortcuts import render
from tax_calculation.models import CustomTariff

# Create your views here.

class Ett_handler:
    def __init__(self, request):
        self.code = request.POST.get('code')
        self.mass = request.POST.get('mass')
        self.price = request.POST.get('price')
        self.tax = CustomTariff.objects.get(tnved_code=self.code).tax

    def get_parameters(self):
        return {'code' : self.code, 'mass' : self.mass, 'price' : self.price, 'tax' : self.tax}

    def tax_type_checker(self):
        if (len(self.tax) <= 3 and self.tax[-1] == "%") or self.tax == "0":
            self.tax_type = 'advalore'
        elif len(self.tax.split()) == 1:
            self.tax_type = 'specific'
        else:
            self.tax_type = 'combine'
        return self.tax_type

    def calculate_tax(self):
        tax_type = self.tax_type_checker()
        if tax_type == 'advalore':
            tax = int(self.price) * (int(self.tax[:-1]) / 100)
            return tax


def index(request):
    return render(request, 'index.html')

def calculate_tax(request):
    handler = Ett_handler(request)
    tax_type = handler.tax_type_checker()
    parameters = handler.get_parameters()
    parameters['tax_type'] = tax_type
    #Проверка на достаточность данных для рассчета по адвалорной формуле. Если данных недостаточно, запрашиваем дополнительные, если достаточно, производим рассчет.
    if tax_type == 'advalore':
        print(parameters['price'])
        if parameters['price'] == '':
            return render(request, 'result.html', context=parameters)
        else:
            calculated_tax = handler.calculate_tax()
            parameters['calculated_tax'] = calculated_tax
            return render(request, 'result.html', context=parameters)
    #Проверка на достаточность данных для рассчета по специфической формуле. Если данных недостаточно, запрашиваем дополнительные если достаточно, производим рассчет.
    elif tax_type == 'specific':
        if parameters['mass'] == '':
            return render(request, 'result.html', context=parameters)
    #Проверка на достаточность данных для рассчета по комбинированной формуле. Если данных недостаточно, запрашиваем дополнительные если достаточно, производим рассчет.
    elif tax_type == 'combine':
        if parameters['mass'] == '' or parameters['price'] == '':
            return render(request, 'result.html', context=parameters)