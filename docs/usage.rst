========
Usage
========

Nearly every project breaks payment types into two broad categories, and will support either or both:

1. Ongoing Subscriptions (Well supported)
2. Individual Checkouts (Early, undocumented support)

Ongoing Subscriptions
=====================

dj-stripe provides three methods to support ongoing subscriptions:

* Middleware approach to constrain entire projects easily.
* Class-Based View mixin to constrain individual views.
* View decoration to constrain Function-based views.

.. warning:: **anonymous** users always raise a ``ImproperlyConfigured`` exception.

     When **anonymous** users encounter these components they will raise a ``django.core.exceptions.ImproperlyConfigured`` exception. This is done because dj-stripe is not an authentication system, so it does a hard error to make it easier for you to catch where content may not be behind authentication systems.

Any project can use one or more of these methods to control access. 


Constraining Entire Sites
-------------------------

If you want to quickly constrain an entire site, the ``djstripe.middleware.SubscriptionPaymentMiddleware`` middleware does the following to user requests:

* **authenticated** users are redirected to ``djstripe.views.SubscribeFormView`` unless they...:

    * ... have a valid subscription --or--
    * ... are not ``user.is_staff==True``.

* **anonymous** users always raise a ``django.core.exceptions.ImproperlyConfigured`` exception when they encounter these systems. This is done because dj-stripe is not an authentication system. 

----

**Example:**

Step 1: Add the middleware:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        ...
        'djstripe.middleware.SubscriptionPaymentMiddleware',
        ...
        )

Step 2: Specify exempt URLS:

.. code-block:: python

    # sample only - customize to your own needs!
    # djstripe pages are automatically exempt!
    DJSTRIPE_SUBSCRIPTION_REQUIRED_EXCEPTION_URLS = (
        'home',
        'about',
        "(allauth)",  # anything in the django-allauth URLConf

    )

Using this example any request on this site that isn't on the homepage, about, accounts, or djstripe pages is redirected to ``djstripe.views.SubscribeFormView``/

.. seealso::

    * :doc:`settings`

Constraining Class-Based Views
------------------------------

If you want to quickly constrain a single Class-Based View, the ``djstripe.mixins.SubscriptionPaymentRequiredMixin`` mixin does the following to user requests:

* **authenticated** users are redirected to ``djstripe.views.SubscribeFormView`` unless they...:

    * ... have a valid subscription --or--
    * ... are not ``user.is_staff==True``.

* **anonymous** users always raise a ``django.core.exceptions.ImproperlyConfigured`` exception when they encounter these systems. This is done because dj-stripe is not an authentication system. 

----

**Example:**

.. code-block:: python

    # import necessary Django stuff
    from django.views.generic import View
    from django.http import HttpResponse

    # dependency of dj-stripe so it's garanteed to be there.
    from braces.views import LoginRequiredMixin  

    # import the incredible, edible mixin!
    from djstripe.mixins import SubscriptionPaymentRequiredMixin

    class MyConstrainedView(
            LoginRequiredMixin,  # Checks authentication
            SubscriptionPaymentRequiredMixin,  # Checks for valid subscription
            View
        ):

        def get(self, request, *args, **kwargs):
            return HttpReponse("I like cheese")


Constraining Function-Based Views
---------------------------------

If you want to quickly constrain a single Function-Based View, the ``djstripe.decorators.subscription_payment_required`` decorator does the following to user requests:

* **authenticated** users are redirected to ``djstripe.views.SubscribeFormView`` unless they...:

    * ... have a valid subscription --or--
    * ... are not ``user.is_staff==True``.

* **anonymous** users always raise a ``django.core.exceptions.ImproperlyConfigured`` exception when they encounter these systems. This is done because dj-stripe is not an authentication system. 

----

**Example:**

.. code-block:: python

    # import necessary Django stuff
    from django.contrib.auth.decorators import login_required
    from django.http import HttpResponse

    # import the wonderful decorator
    from djstripe.decorators import subscription_payment_required

    @login_required
    @subscription_payment_required
    def my_constrained_view(request):
        return HttpReponse("I like cheese")


Don't do this!
---------------

Described is an anti-pattern. View logic belongs in views.py, not urls.py.

.. code-block:: python

    # DON'T DO THIS!!!
    from django.conf.urls import patterns, url
    from django.contrib.auth.decorators import login_required
    from djstripe.decorators import subscription_payment_required

    from contents import views

    urlpatterns = patterns("",

        # Class-Based View anti-pattern
        url(
            r"^content/$",

            # Not using decorators as decorators
            # Harder to see what's going on
            login_required(
                subscription_payment_required(
                    views.ContentDetailView.as_view()
                )
            ),
            name="content_detail"
        ),
        # Function-Based View anti-pattern
        url(
            r"^content/$",

            # Example with function view
            login_required(
                subscription_payment_required(
                    views.content_list_view
                )
            ),
            name="content_detail"
        ),
    )

Subscriptions + Registration
=============================

This requires the following additional requirements:

* django-allauth (user registration)
* django-crispy-forms (form rendering)
* django-floppyforms (widget rendering)

Additional Settings (settings.py):

.. code-block:: python

    # django.contrib.sites is also necessary
    INSTALLED_APPS += (
        "floppyforms",
        "allauth",  # registration
        "allauth.account",  # registration
    )
    TEMPLATE_CONTEXT_PROCESSORS += (
        "allauth.account.context_processors.account",
    )
    AUTHENTICATION_BACKENDS = (
        "django.contrib.auth.backends.ModelBackend",
        "allauth.account.auth_backends.AuthenticationBackend",
    )
    ACCOUNT_AUTHENTICATION_METHOD = "username"
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    ACCOUNT_SIGNUP_FORM_CLASS = "djstripe.forms.StripeSubscriptionSignupForm"
    SITE_ID = 1

Necessary URLS (root URLConf):

.. code-block:: python

    (r'^accounts/', include('allauth.urls')),
    

Try it out!:

* http://127.0.0.1:8000/accounts/signup

**Note:**

If you override allauth's signup template you'll need to make sure it includes
the critical elements dj-stripe's version found at https://raw.github.com/pydanny/dj-stripe/master/djstripe/templates/account/signup.html
