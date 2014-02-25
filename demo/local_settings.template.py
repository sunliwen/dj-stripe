
import os

STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "<public_key>")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "<secret_key>")

import sys

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'formatter': 'verbose',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # # Enable sql log
        # 'django.db.backends': {
        #     'handlers': ['null'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': []
        }
    }
}