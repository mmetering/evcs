from django.contrib import admin
from evcs.models import RFID, ChargingStation

admin.site.register(ChargingStation)
admin.site.register(RFID)
