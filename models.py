from django.db import models
from mmetering.models import Flat


class RFID(models.Model):
    """
    Models the RFID chip and creates adds a relation to a certain flat.
    """
    serial = models.CharField(max_length=128)
    flat = models.ForeignKey(Flat)

    def __str__(self):
        return "RFID von " + self.flat.name

    class Meta:
        verbose_name = "RFID"
        verbose_name_plural = "RFIDs"


class ChargingStartValue(models.Model):
    """
    Saves the meter value at the start of the charging process.
    """
    rfid = models.ForeignKey(RFID, verbose_name='RFID')
    time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "EVCS-Startwert für " + self.rfid.flat.name


class ChargingEndValue(models.Model):
    """
    Saves the meter value at the end of the charging process.
    """
    rfid = models.ForeignKey(RFID)
    start = models.ForeignKey(ChargingStartValue, on_delete=models.CASCADE)
    time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "EVCS-Endwert für " + self.rfid.flat.name
