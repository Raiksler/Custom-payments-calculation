from django.shortcuts import render
from nds.models import Nds

# Create your views here.

class Db_manager:

    def get_nds(self, code):
        return Nds.objects.filter(tnved_code=code).values('nds','title')


def index(request):
    return render(request, 'nds/index.html')

def result(request):
    database = Db_manager()
    chosen_nds = request.POST.get('chosen_nds')
    code = request.POST.get('code')
    price = request.POST.get('price')
    nds = database.get_nds(code)            # Имеется ввиду кластер ставок ндс для конкретного товарного кода.
    payment = ''
    if chosen_nds != None:
        payment = int(chosen_nds) / 100 * int(price)
    return render(request, 'nds/result.html', context={'code' : code, 'nds' : nds, 'chosen_nds' : chosen_nds, 'price' : price, 'payment' : payment})