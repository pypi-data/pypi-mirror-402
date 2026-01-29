from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.utils import ErrorList

from django.conf import settings

from django.contrib.contenttypes.models import ContentType

from .models import ContentLicenceRegistry

from .mixins import LicencingFormMixin, HELP_TEXTS
'''
    self.instance is the ContentLicenceRegistry instance
    self.content_instance is the content_instance which content_fields will be licenced

    the form can be initialized with or without the instance to be licenced in order to make
    it usable together with the creation of the instance. however, the save() method
    can only be called if self.content_instance is not None
'''

class ContentLicencingForm(LicencingFormMixin, forms.ModelForm):

    content_field = None
    
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, content_instance=None, content_field=None):
        
        self.content_instance = content_instance

        if content_field is not None:
            self.content_field = content_field

        if not self.content_field:
            raise ValueError('ContentLicencingForm needs a content_field attribute')

        # ContentLicencingForm never receives an instance. The instance is fetched using the content_instance
        # and the field
        if self.content_instance is not None:
            instance = self.get_licence_registry_entry(self.content_instance)
            

        super().__init__(data=data, files=files, auto_id=auto_id, prefix=prefix,
                                           initial=initial, error_class=error_class, label_suffix=label_suffix,
                                           empty_permitted=empty_permitted, instance=instance)

        
    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """
        """
        Register the licence with the given content_instance and content_field
        """

        if self.content_instance is None:
            raise ValueError("ContentLicencingForm can only be save if it has self.content_instance")
        
        return super().save(commit=commit)


    def get_licence_registry_entry(self, instance):

        instance_content_type = ContentType.objects.get_for_model(instance)
        
        licencing_instance = ContentLicenceRegistry.objects.filter(
            content_type = instance_content_type,
            object_id = instance.pk,
            model_field = self.content_field,
        ).first()

        return licencing_instance
        

    class Meta:
        model = ContentLicenceRegistry
        fields = ["creator_name", "creator_link", "source_link", "licence", "licence_version", "uploader"]

        widgets = {
            "source_link" : forms.TextInput,
            "uploader" : forms.HiddenInput,
        }

        help_texts = HELP_TEXTS
    
    
