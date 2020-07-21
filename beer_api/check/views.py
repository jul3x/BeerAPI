from django.shortcuts import render
from .models import UploadFileForm


def check(request, template_name='check.html'):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            return render(request, template_name, {'form': form, 'exists': check_if_exists(request.FILES['file'])})
    else:
        form = UploadFileForm()

    return render(request, template_name, {'form': form, 'exists': None})


def check_if_exists(file):
    return True
