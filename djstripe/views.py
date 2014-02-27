from __future__ import unicode_literals
import json

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import TemplateView
from django.views.generic import View

from braces.views import CsrfExemptMixin
from braces.views import FormValidMessageMixin
from braces.views import LoginRequiredMixin
from braces.views import SelectRelatedMixin
from braces.views import JsonRequestResponseMixin

import stripe

from .forms import OneTimeForm, MonthlyForm, PlanForm, CancelSubscriptionForm
from .mixins import PaymentsContextMixin, SubscriptionMixin, OneTimeMixin
from .models import CurrentSubscription
from .models import Customer
from .models import Event
from .models import EventProcessingException
from .settings import PLAN_LIST
from .settings import PY3
from .settings import User
from .sync import sync_customer


class ChangeCardView(LoginRequiredMixin, PaymentsContextMixin, DetailView):
    # TODO - needs tests
    # Needs a form
    # Not done yet
    template_name = "djstripe/change_card.html"

    def get_object(self):
        if hasattr(self, "customer"):
            return self.customer
        self.customer, created = Customer.get_or_create(self.request.user)
        return self.customer

    def post(self, request, *args, **kwargs):
        customer = self.get_object()
        try:
            send_invoice = customer.card_fingerprint == ""
            customer.update_card(
                request.POST.get("stripe_token")
            )
            if send_invoice:
                customer.send_invoice()
            customer.retry_unpaid_invoices()
        except stripe.CardError as e:
            messages.info(request, "Stripe Error")
            return render(
                request,
                self.template_name,
                {
                    "customer": self.get_object(),
                    "stripe_error": e.message
                }
            )
        messages.info(request, "Your card is now updated.")
        return redirect("djstripe:account")


class CancelSubscriptionView(LoginRequiredMixin, PaymentsContextMixin, FormView):
    # TODO - needs tests
    template_name = "djstripe/cancel_subscription.html"
    form_class = CancelSubscriptionForm

    def form_valid(self, form):
        customer, created = Customer.get_or_create(self.request.user)
        # TODO - pass in setting to control at_period_end boolean
        current_subscription = customer.cancel_subscription(at_period_end=True)
        if current_subscription.status == current_subscription.STATUS_CANCELLED:
            messages.info(self.request, "Your account is now cancelled.")
        else:
            messages.info(self.request, "Your account status is now '{a}' until '{b}'".format(
                    a=current_subscription.status, b=current_subscription.current_period_end)
            )

        return redirect("djstripe:account")


class WebHook(CsrfExemptMixin, JsonRequestResponseMixin, View):
    require_json = True

    def post(self, request, *args, **kwargs):
        data = self.request_json
        if Event.objects.filter(stripe_id=data["id"]).exists():
            EventProcessingException.objects.create(
                data=data,
                message="Duplicate event record",
                traceback=""
            )
        else:
            event = Event.objects.create(
                stripe_id=data["id"],
                kind=data["type"],
                livemode=data["livemode"],
                webhook_message=data
            )
            event.validate()
            event.process()
        return HttpResponse()


class HistoryView(LoginRequiredMixin, SelectRelatedMixin, DetailView):
    # TODO - needs tests
    template_name = "djstripe/history.html"
    model = Customer
    select_related = ["invoice"]

    def get_object(self):
        customer, created = Customer.get_or_create(self.request.user)
        return customer


class SyncHistoryView(CsrfExemptMixin, LoginRequiredMixin, View):
    # TODO - needs tests
    def post(self, request, *args, **kwargs):
        return render(
            request,
            "djstripe/includes/_history_table.html",
            {"customer": sync_customer(request.user)}
        )


class AccountView(LoginRequiredMixin, SelectRelatedMixin, TemplateView):
    # TODO - needs tests
    template_name = "djstripe/account.html"

    def get_context_data(self, *args, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        customer, created = Customer.get_or_create(self.request.user)
        context['customer'] = customer
        try:
            context['subscription'] = customer.current_subscription
        except CurrentSubscription.DoesNotExist:
            context['subscription'] = None
        context['plans'] = PLAN_LIST
        return context


################## Subscription views


class SubscribeFormView(
        LoginRequiredMixin,
        FormValidMessageMixin,
        SubscriptionMixin,
        FormView):
    # TODO - needs tests

    form_class = PlanForm
    template_name = "djstripe/subscribe_form.html"
    success_url = reverse_lazy("djstripe:history")
    form_valid_message = "You are now subscribed!"

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            try:
                customer, created = Customer.get_or_create(self.request.user)
                customer.update_card(self.request.POST.get("stripe_token"))
                customer.subscribe(form.cleaned_data["plan"])
            except stripe.StripeError as e:
                # add form error here
                self.error = e.args[0]
                return self.form_invalid(form)
            # redirect to confirmation page
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ChangePlanView(LoginRequiredMixin,
                        FormValidMessageMixin,
                        SubscriptionMixin,
                        FormView):

    form_class = PlanForm
    template_name = "djstripe/subscribe_form.html"
    success_url = reverse_lazy("djstripe:history")
    form_valid_message = "You've just changed your plan!"

    def post(self, request, *args, **kwargs):
        form = PlanForm(request.POST)
        customer = request.user.customer
        if form.is_valid():
            try:
                customer.subscribe(form.cleaned_data["plan"])
            except stripe.StripeError as e:
                self.error = e.message
                return self.form_invalid(form)
            except Exception as e:
                raise e
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


######### Donate One Time View


class DonateOneTimeView(
        FormValidMessageMixin,
        OneTimeMixin,
        FormView):
    # TODO - needs tests
    """email and card information will be used to charge
    """

    form_class = OneTimeForm
    template_name = "djstripe/onetime_form.html"
    success_url = "./thanks/" # reverse_lazy("djstripe:thanks")
    form_valid_message = "Thanks for your donation!"

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        metadata = {
            'firstname': self.request.POST.get("firstname"),
            'lastname': self.request.POST.get("lastname"),
            'name': self.request.POST.get("name"),
            'email': self.request.POST.get("email"),
            'donationDesignations': self.request.POST.get("donationDesignations"),
            'additionalInfos': ",".join(self.request.POST.getlist("additionalInfos")),
            'comment': self.request.POST.get("comment"),
        }
        if form.is_valid():
            try:
                description = "Charge for one time donation for info@bmsis.com"
                cus = stripe.Customer.create(
                    metadata=metadata,
                    description="Donator for Blue Marble Space",
                    card=self.request.POST.get("stripe_token"),
                    email=self.request.POST.get("email"),
                )
                stripe.InvoiceItem.create(
                    metadata=metadata,
                    customer=cus["id"],
                    amount=int(form.cleaned_data["amount"]) * 100,
                    currency="usd",
                    description=description
                )
                invoice = stripe.Invoice.create(
                    customer=cus["id"],
                    description=description
                )
                invoice.pay()
            except stripe.StripeError as e:
                # add form error here
                self.error = e.args[0]
                return self.form_invalid(form)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


######### Donate Monthly View

class DonateMonthlyView(
        FormValidMessageMixin,
        OneTimeMixin,
        FormView):
    # TODO - needs tests
    """email and card information will be used to charge
    """

    form_class = MonthlyForm
    template_name = "djstripe/monthly_form.html"
    success_url = "./thanks/"  # reverse_lazy("djstripe:thanks")
    form_valid_message = "Thanks for your donation!"

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            try:
                try:
                    # HACKY
                    quantity = int(self.request.POST.get("amount")) or 1
                except Exception:
                    quantity = 1
                description = "Charge for monthly donation for info@bmsis.com"
                stripe.Customer.create(
                    metadata={
                        'fullname': self.request.POST.get("fullname"),
                        'email': self.request.POST.get("email"),
                        'donationDesignations': self.request.POST.get("donationDesignations"),
                        'additionalInfos': ",".join(self.request.POST.getlist("additionalInfos")),
                        'comment': self.request.POST.get("comment"),
                    },
                    description=description,
                    card=self.request.POST.get("stripe_token"),
                    email=self.request.POST.get("email"),
                    plan=self.request.POST.get("plan"),
                    quantity=quantity,
                )

            except stripe.StripeError as e:
                # add form error here
                self.error = e.args[0]
                return self.form_invalid(form)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


######### Web services
class CheckAvailableUserAttributeView(View):

    def get(self, request, *args, **kwargs):
        attr_name = self.kwargs['attr_name']
        not_available = User.objects.filter(
                **{attr_name: request.GET.get("v", "")}
        ).exists()
        return HttpResponse(json.dumps(not not_available))
