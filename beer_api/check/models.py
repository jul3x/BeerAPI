from django import forms
from django.db import models


class CapImage(models.Model):
    name = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to='images')


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Image file')
