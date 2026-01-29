from django import forms

from .licences import ContentLicence
from .widgets import LicenceSelectWidget

class LicenceField(forms.MultiValueField):

    widget = LicenceSelectWidget

    def __init__(self, *args, **kwargs):
        
        fields = (
            forms.CharField(),
            forms.CharField(),
        )
        super().__init__(fields, *args, **kwargs)


    def compress(self, data_list):

        if data_list and len(data_list) == 2 and len(data_list[0]) > 0 and len(data_list[1]) >0:

            short_name = data_list[0]
            version = data_list[1]

            content_licence = ContentLicence(short_name, version)

            return content_licence

        return None
