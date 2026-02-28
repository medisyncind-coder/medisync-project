from django.shortcuts import render

# ---------------- HOME / COMMON ---------------- #

def home(request):
    return render(request, 'index.html')
