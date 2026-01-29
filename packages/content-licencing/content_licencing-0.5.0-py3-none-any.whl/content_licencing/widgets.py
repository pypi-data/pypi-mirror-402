from django.conf import settings
from django.forms.widgets import MultiWidget
from django.forms import Select
from django.template import loader, Context

from .licences import ContentLicence, DEFAULT_LICENCE, LICENCE_CHOICES, LICENCE_VERSION_CHOICES

class LicenceSelectWidget(MultiWidget):

    template_name = 'content_licencing/widgets/licence_select_widget.html'

    def __init__(self, attrs={}):
        
        widgets = (
            Select(choices=LICENCE_CHOICES, attrs=attrs), # licence short_name
            Select(attrs=attrs), # licence version, choices depend on licence
        )
        super().__init__(widgets, attrs)
        

    def decompress(self, content_licence):

        if content_licence is None:
            return [None, None]

        data_list = [content_licence.short_name, content_licence.version]
        
        return data_list


    def get_context(self, name, value, attrs):

        if not value:
            value = DEFAULT_LICENCE

        if not isinstance(value, list):
            value = self.decompress(value)

        self.widgets[1].choices = LICENCE_VERSION_CHOICES[value[0]]
        
        context = super().get_context(name, value, attrs)


        template_version_choices = {}

        for short_name, versions in LICENCE_VERSION_CHOICES.items():

            choices = sorted([version_tuple[0] for version_tuple in versions])
            template_version_choices[short_name] = choices

        final_attrs = context['widget']['attrs']
        id_ = final_attrs.get('id')

        context['licence_version_choices'] = template_version_choices
        context['id_base'] = id_

        return context
