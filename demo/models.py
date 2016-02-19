from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Location(models.Model):
    zip = models.CharField(max_length=5)
    lat = models.FloatField()
    lng = models.FloatField()
