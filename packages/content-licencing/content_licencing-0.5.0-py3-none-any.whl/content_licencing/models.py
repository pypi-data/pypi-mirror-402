from django.db import models
from django.conf import settings

from . import settings as content_licencing_settings

try:
    from django.contrib.contenttypes.generic import GenericForeignKey
except:
    from django.contrib.contenttypes.fields import GenericForeignKey

from django.contrib.contenttypes.models import ContentType

from django.db.models.fields.files import ImageFieldFile

import hashlib

from .licences import LICENCE_CHOICES, ContentLicence

'''
    Model to maintain licensing of user generated/uploaded content. This covers
    e.g. images and text.

    There a serveral use cases:
    1. User uploads content he does not own, but which he is allowed to use

    2. user uploads content he created

    3. user creates content which is changed by others afterwards
    - contributors is used

    if an image is used on several locations, every location will be registered in the
    registry

    To prefill a licence form if the same image is uploaded again, a sha256 is stored
'''

class ContentLicenceRegistryManager(models.Manager):

    # the register method registers newly created content and adds
    # users to contributors if the object already is registered
    # the licence is not changed if it already existed
    def register(self, instance, field, user, licence, licence_version, **kwargs):

        licence_reg = self.model.objects.filter(
            content_type = ContentType.objects.get_for_model(instance),
            object_id = instance.id,
            model_field = field,
        ).first()
        
        if licence_reg:
            # update kwargs
            for key, value in kwargs.items():
                setattr(licence_reg, key, value)

        else:

            # add uploader in creation
            # if the owner differs from the uploader, this has to be in kwargs
            licence_reg = self.model(
                content_type = ContentType.objects.get_for_model(instance),
                object_id = instance.id,
                model_field = field,
                uploader = user,
                **kwargs
            )
            
        licence_reg.licence = licence
        licence_reg.licence_version = licence_version
        licence_reg.save()


        if user != licence_reg.uploader:
            licence_reg.contributors.add(user)

        # cannot return instance - it can be multiple fields resulting in multiple registry entries


class ContentLicenceRegistry(models.Model):

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    content = GenericForeignKey('content_type', 'object_id')
    model_field = models.CharField(max_length=255)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True) # the user who inserted text/images into a form field
    uploaded_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    licence = models.CharField(max_length=100, choices=LICENCE_CHOICES,
                               default=content_licencing_settings.CONTENT_LICENCING_DEFAULT_LICENCE)
    licence_version = models.CharField(max_length=10)
    creator_name = models.CharField(max_length=355) # first an last name/ company name of the owner, if not the user
    creator_link = models.CharField(max_length=355, null=True, blank=True) # link to owner website
    source_link = models.TextField(null=True, blank=True) # direct link to source text/source image
    language = models.CharField(max_length=15, null=True)
    sha256 = models.CharField(max_length=355)

    contributors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='contributors')

    objects = ContentLicenceRegistryManager()

    def content_licence(self):
        return ContentLicence(self.licence, self.licence_version)

    def save(self, *args, **kwargs):
        content = getattr(self.content, self.model_field)
        if type(content) == ImageFieldFile:
            with open(content.path, "rb") as f:
                self.sha256 = hashlib.sha256(f.read()).hexdigest()
        elif type(content) == str:
            self.sha256 = hashlib.sha256(content.encode()).hexdigest()
        else:
            self.sha256 = hashlib.sha256(content).hexdigest()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('content_type', 'object_id', 'model_field', 'language')

        
        
