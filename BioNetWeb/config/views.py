from django.shortcuts import render

# Create your views here.
def create(request):
    if request.method == 'POST':
        
    return render(request, 'config/create.html', {'observables': ['test1', 'test2']})
