from django import forms
from django.db import models


class CapImage(models.Model):
    name = models.CharField(max_length=255, blank=True)
    hash_data = models.CharField(null=True, max_length=2048)
    photo = models.ImageField(upload_to='images')


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Image file')
