from . import settings

# create licencing choices from settings
LICENCE_CHOICES = []

LICENCE_VERSION_CHOICES = {
}

# default is the lates available version
LICENCE_DEFAULT_VERSIONS = {}

LICENCE_LOOKUP = {} 



for choice in settings.CONTENT_LICENCING_LICENCES:
    licence_choice = (
        choice['short_name'], choice['full_name']
    )

    LICENCE_CHOICES.append(licence_choice)

    LICENCE_LOOKUP[choice['short_name']] = {}

    version_choices = []
    latest_version = None
    for version, link in choice['versions'].items():

        if latest_version == None or float(version) > float(latest_version):
            latest_version = version
        
        version_choice = (
            version, version
        )
        version_choices.append(version_choice)

        # add to lookup
        LICENCE_LOOKUP[choice['short_name']][version] = {
            'full_name' : choice['full_name'],
            'link' : link,
        }

    LICENCE_VERSION_CHOICES[choice['short_name']] = version_choices
    LICENCE_DEFAULT_VERSIONS[choice['short_name']] = latest_version    


class ContentLicence:

    def __init__(self, short_name, version=None):
        self.short_name = short_name

        if version == None:
            version = LICENCE_DEFAULT_VERSIONS[short_name]
        
        self.version = version

        self.link = LICENCE_LOOKUP[self.short_name][self.version]['link']

    def as_dict(self):
        
        
        dic = {
            'short_name' : self.short_name,
            'version' : self.version,
            'link' : self.link,
        }

        return dic

        
DEFAULT_LICENCE = ContentLicence(settings.CONTENT_LICENCING_DEFAULT_LICENCE['short_name'],
                                 settings.CONTENT_LICENCING_DEFAULT_LICENCE['version'])
