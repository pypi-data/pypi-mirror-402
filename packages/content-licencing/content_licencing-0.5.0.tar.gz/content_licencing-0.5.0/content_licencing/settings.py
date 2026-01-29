from django.conf import settings

# content_licencing
DEFAULT_CONTENT_LICENCING_LICENCES = [
    {'short_name' : 'All Rights Reserved', 'full_name':'All Rights Reserved', 'versions':{
            '1.0': None,
        },
    },
    {'short_name' : 'PDM', 'full_name': 'Public Domain Mark', 'versions':{
            '1.0' : 'https://creativecommons.org/publicdomain/mark/1.0/',
        },
    },
    {'short_name' : 'CC0', 'full_name':'Public Domain Dedication', 'versions':{
            '1.0' : 'https://creativecommons.org/publicdomain/zero/1.0/',
        },
    },
    {'short_name' : 'CC BY', 'full_name':'Creative Commons Attribution', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by/4.0/',
        },
    },
    {'short_name' : 'CC BY-SA', 'full_name':'Creative Commons Attribution-ShareAlike', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by-sa/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by-sa/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by-sa/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by-sa/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by-sa/4.0/',
        },
    },
    {'short_name' : 'CC BY-ND', 'full_name':'Creative Commons Attribution-NoDerivs', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by-nd/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by-nd/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by-nd/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by-nd/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by-nd/4.0/',
        },
    },
    {'short_name' : 'CC BY-NC', 'full_name':'Creative Commons Attribution-NonCommercial', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by-nc/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by-nc/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by-nc/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by-nc/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by-nc/4.0/',
        },
    },
    {'short_name' : 'CC BY-NC-SA', 'full_name':'Creative Commons Attribution-NonCommercial-ShareAlike', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by-nc-sa/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by-nc-sa/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by-nc-sa/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        },
    },
    {'short_name' : 'CC BY-NC-ND', 'full_name':'Creative Commons Attribution-NonCommercial-NoDerivs', 'versions':{
            '1.0' : 'https://creativecommons.org/licenses/by-nc-nd/1.0/',
            '2.0' : 'https://creativecommons.org/licenses/by-nc-nd/2.0/',
            '2.5' : 'https://creativecommons.org/licenses/by-nc-nd/2.5/',
            '3.0' : 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
            '4.0' : 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        },
    },
]

DEFAULT_CONTENT_LICENCING_DEFAULT_LICENCE = {
    'short_name' : 'CC0',
    'version' : '1.0',
}


CONTENT_LICENCING_LICENCES = getattr(settings, 'CONTENT_LICENCING_LICENCES', DEFAULT_CONTENT_LICENCING_LICENCES)

CONTENT_LICENCING_DEFAULT_LICENCE = getattr(settings, 'CONTENT_LICENCING_DEFAULT_LICENCE',
                                            DEFAULT_CONTENT_LICENCING_DEFAULT_LICENCE)
