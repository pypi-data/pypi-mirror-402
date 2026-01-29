from django.conf import settings
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContentLicenceRegistry
from .licences import LICENCE_CHOICES, DEFAULT_LICENCE, ContentLicence
from .fields import LicenceField

HELP_TEXTS = {
    'creator_name' : _('The full name of the entity which created this content. If the content is owned by the public and the original creator is unknown put in your full personal name.'),
    'source_link' : _('Direct link to the image or text'),
    'creator_link' : _('Link to the creators website'),
}


class GetLicenceMixin:

    def get_licence_as_dict(self):

        content_licence = self.cleaned_data['licence']
        
        licence = {
            'creator_name' : self.cleaned_data['creator_name'],
            'licence' : content_licence.as_dict(),
            'creator_link' : self.cleaned_data.get('creator_link', None),
            'source_link' : self.cleaned_data.get('source_link', None),
        }

        return licence


class LicencingFormMixin(GetLicenceMixin, forms.Form):

    creator_name = forms.CharField(help_text=HELP_TEXTS['creator_name'])
    creator_link = forms.CharField(help_text=HELP_TEXTS['creator_link'], required=False)
    source_link = forms.CharField(help_text=HELP_TEXTS['source_link'], required=False)
    licence = LicenceField(initial=DEFAULT_LICENCE)


class OptionalLicencingFormMixin(GetLicenceMixin, forms.Form):
    creator_name = forms.CharField(help_text=HELP_TEXTS['creator_name'], required=False)
    creator_link = forms.CharField(help_text=HELP_TEXTS['creator_link'], required=False)
    source_link = forms.CharField(help_text=HELP_TEXTS['source_link'], required=False)
    licence = LicenceField(initial=DEFAULT_LICENCE, required=False)
    

    
    
