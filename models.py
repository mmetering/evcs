from django.db import models
from mmetering.models import Flat


class EVCSData(models.Model):
    flat = models.ForeignKey(Flat)
    saved_time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "EVCS-Datenwert für " + self.flat.name

    class Meta:
        permissions = (
            ("can_download", "Can download EVCSData"),
            ("can_view", "Can view EVCSData"),
        )
