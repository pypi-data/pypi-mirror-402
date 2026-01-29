from django.contrib.contenttypes.models import ContentType
from .models import ContentLicenceRegistry

class LicencingFormViewMixin:

    # instance might be "None" or something that does not exist
    def set_licence_registry_entry(self, instance, model_field):

        # the licence registry has to be stored for the ImageStore db entry
        self.licence_registry_entry = None
        if instance:
            content_type = ContentType.objects.get_for_model(instance)
            self.licence_registry_entry = ContentLicenceRegistry.objects.filter(content_type=content_type,
                                            object_id=instance.id, model_field=model_field).first()
        

    def get_licencing_initial(self):
        initial = {}
        
        if self.licence_registry_entry:
            initial['creator_name'] = self.licence_registry_entry.creator_name
            initial['creator_link'] = self.licence_registry_entry.creator_link
            initial['source_link'] = self.licence_registry_entry.source_link
            initial['licence'] = self.licence_registry_entry.content_licence()

        return initial
    

    def register_content_licence(self, form, instance, model_field):
        # register content licence
        licence_kwargs = {
            'creator_name' : form.cleaned_data['creator_name'],
            'creator_link' : form.cleaned_data['creator_link'],
            'source_link' : form.cleaned_data['source_link'],
        }

        registry_entry = ContentLicenceRegistry.objects.register(instance, model_field, self.request.user,
                            form.cleaned_data['licence'].short_name, form.cleaned_data['licence'].version,
                            **licence_kwargs)
        
