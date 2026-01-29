from django.shortcuts import render
from django.views.generic import FormView

from .forms import ContentLicencingForm


'''
    Subclass of FormView, adding the ModelForm named ContentLinceningForm
    The result is a FormView with two forms: licencing_form and the user defined form
    Support the licencing of one single field
'''
class LicencingFormView(FormView):
    licencing_form_class = ContentLicencingForm

    content_field = None

    def __init__(self, **kwargs):

        self.content_instance = None
        super().__init__(**kwargs)

        if not self.content_field:
            raise ValueError("LicencingFormView needs a content_field attribute")


    def get_licencing_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the licencing form.
        """
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'content_field' : self.content_field,
        }

        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })

        # ContentLicencingForm fetches the ContentLicenceRegistry Instance using content_instance and content_field
        if hasattr(self, 'content_instance'):
            kwargs.update({'content_instance': self.content_instance})

        return kwargs

    def get_licencing_form_class(self):
        """
        Returns the form class to use in this view
        """
        return self.licencing_form_class

    def get_licencing_form(self, licencing_form_class=None):
        """
        Returns an instance of the licencing form to be used in this view.
        """
        if licencing_form_class is None:
            licencing_form_class = self.get_licencing_form_class()
        return licencing_form_class(**self.get_licencing_form_kwargs())
    

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates a blank version of the form.
        """
        form = self.get_form()
        licencing_form = self.get_licencing_form()
        return self.render_to_response(self.get_context_data(form=form, licencing_form=licencing_form))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form = self.get_form()
        licencing_form = self.get_licencing_form()
        if form.is_valid() and licencing_form.is_valid():
            return self.form_valid(form, licencing_form)
        else:
            return self.form_invalid(form, licencing_form)


    def form_valid(self, form, licencing_form):
        """
        The superclass (FormView) only accepts form
        if the form_view has a content_instance, create self.object
        """
        if self.content_instance:
            self.object = licencing_form.save()
        return super().form_valid(form)

    def form_invalid(self, form, licencing_form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        return self.render_to_response(self.get_context_data(form=form, licencing_form=licencing_form))

