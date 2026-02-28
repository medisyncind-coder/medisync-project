from django.contrib import admin
from . models import Doctor, Lab, LabTest


admin.site.register(Doctor)

admin.site.register(Lab)

admin.site.register(LabTest)