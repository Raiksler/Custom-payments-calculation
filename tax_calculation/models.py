from django.db import models

# Create your models here.

class CustomTariff(models.Model):
    tnved_code = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=2000, blank=True, null=True)
    tax = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'custom_tariff'