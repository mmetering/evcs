from django.db import models
from mmetering.models import Flat


class ChargingStation(models.Model):
    """
    Models a charging station with it's name and a unique hardware address.
    """
    name = models.CharField(max_length=20)

    # TODO: change max_length to actual address length
    hardware_address = models.CharField(max_length=200, verbose_name="Hardware Adresse")

    class Meta:
        verbose_name = "Tankstelle"
        verbose_name_plural = "Tankstellen"


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


class ChargingValue(models.Model):
    """
    Saves the meter value of the charging process.
    """
    rfid = models.ForeignKey(RFID, verbose_name='RFID')
    charging_station = models.ForeignKey(ChargingStation)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    start_value = models.FloatField()
    end_value = models.FloatField()

    def __str__(self):
        return "EVCS-Wert für " + self.rfid.flat.name
