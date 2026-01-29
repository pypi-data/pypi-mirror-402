from django.contrib.gis.admin import GISModelAdmin
from .forms.widgets import WMTSWidget, WMTSWithSearchWidget


class WMTSGISModelAdmin(GISModelAdmin):
    gis_widget = WMTSWidget


class WMTSGISWithSearchModelAdmin(GISModelAdmin):
    gis_widget = WMTSWithSearchWidget
