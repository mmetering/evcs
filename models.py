from django.db import models
from mmetering.models import Flat


class ChargingValue(models.Model):
    """
    Saves the meter value of the charging process.
    """
    rfid = models.CharField(max_length=30, verbose_name='RFID')
    charging_station = models.ForeignKey(Flat)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    start_value = models.FloatField(null=True)
    end_value = models.FloatField(null=True)

    def __str__(self):
        return "EVCS-Wert für Lader %d" % self.charging_station
