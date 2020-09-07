from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from django_tables2 import RequestConfig
import logging
import sys
from copy import deepcopy
import datetime


from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import ManyToManyField, ProtectedError
from django.forms import Form, ModelMultipleChoiceField, MultipleHiddenInput, Textarea
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.views.generic import View
from django_tables2 import RequestConfig

from extras.models import CustomField, CustomFieldValue, ExportTemplate
from extras.querysets import CustomFieldQueryset
from utilities.exceptions import AbortTransaction
from utilities.forms import BootstrapMixin, CSVDataField
from utilities.utils import csv_format, prepare_cloned_fields
from utilities.error_handlers import handle_protectederror
from utilities.forms import ConfirmationForm, ImportForm
from utilities.paginator import EnhancedPaginator

from extras.models import Graph
from utilities.views import (
    BulkDeleteView, BulkEditView, BulkImportView, ObjectDeleteView, ObjectEditView, ObjectListView,
)


from . import forms
from . import filters
from . import tables
from circuits.models import CircuitType
from circuits.tables import CircuitTypeTable
from .models import Payment, ContractFile
from utilities.views import GetReturnURLMixin


# Create your views here.


class PaymentDeleteView(GetReturnURLMixin, View):
    """
    Delete a single object.

    model: The model of the object being deleted
    template_name: The name of the template
    """
    model = None
    template_name = 'utilities/obj_delete.html'

    def get_object(self, kwargs):
        # Look up object by slug if one has been provided. Otherwise, use PK.
        if 'slug' in kwargs:
            return get_object_or_404(self.model, slug=kwargs['slug'])
        else:
            return get_object_or_404(self.model, pk=kwargs['pk'])

    def get(self, request, **kwargs):
        obj = self.get_object(kwargs)
        form = ConfirmationForm(initial=request.GET)

        return render(request, self.template_name, {
            'obj': obj,
            'form': form,
            'obj_type': self.model._meta.verbose_name,
            'return_url': self.get_return_url(request, obj),
        })

    def post(self, request, **kwargs):
        logger = logging.getLogger('netbox.views.ObjectDeleteView')
        obj = self.get_object(kwargs)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            logger.debug("Form validation was successful")

            try:
                obj.delete()
            except ProtectedError as e:
                logger.info(
                    "Caught ProtectedError while attempting to delete object")
                handle_protectederror(obj, request, e)
                return redirect(obj.get_absolute_url())

            msg = 'Deleted {} {}'.format(self.model._meta.verbose_name, obj)
            logger.info(msg)
            messages.success(request, msg)

            return_url = form.cleaned_data.get('return_url')
            if return_url is not None and is_safe_url(url=return_url, allowed_hosts=request.get_host()):
                return redirect(return_url)
            else:
                return redirect(self.get_return_url(request, obj))

        else:
            logger.debug("Form validation failed")

        return render(request, self.template_name, {
            'obj': obj,
            'form': form,
            'obj_type': self.model._meta.verbose_name,
            'return_url': self.get_return_url(request, obj),
        })


class PaymentCreate (GetReturnURLMixin, View):
    """
    Create single payment
    """
    model = None
    model_form = None
    template_name = 'utilities/obj_edit.html'

    def get_object(self, kwargs):
        # Look up object by slug or PK. Return None if neither was provided.
        if 'slug' in kwargs:
            return get_object_or_404(self.model, slug=kwargs['slug'])
        elif 'pk' in kwargs:
            return get_object_or_404(self.model, pk=kwargs['pk'])
        return self.model()

    def alter_obj(self, obj, request, url_args, url_kwargs):
        # Allow views to add extra info to an object before it is processed. For example, a parent object can be defined
        # given some parameter from the request URL.
        return obj

    def dispatch(self, request, *args, **kwargs):
        self.obj = self.alter_obj(
            self.get_object(kwargs), request, args, kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Parse initial data manually to avoid setting field values as lists
        initial_data = {k: request.GET[k] for k in request.GET}
        form = self.model_form(instance=self.obj, initial=initial_data)

        return render(request, self.template_name, {
            'obj': self.obj,
            'obj_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(request, self.obj),
        })

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger('netbox.views.ObjectEditView')
        form = self.model_form(request.POST, request.FILES, instance=self.obj)

        if form.is_valid():
            logger.debug("Form validation was successful")

            obj = form.save()
            string = ''
            for value in obj.devices.all():
                if escape(obj) not in value.comments:
                    string = string + ' ' + value.name
                    value.comments = value.comments + \
                        '\n\n Payment link - [{}]({})'.format(
                            escape(obj), obj.get_absolute_url())
                    value.save()

            for circ in obj.circuits.all():
                if escape(obj) not in circ.comments:
                    string = string + ' ' + circ.cid
                    circ.comments = circ.comments + \
                        '\n\n Payment link - [{}]({})'.format(
                            escape(obj), obj.get_absolute_url())
                    circ.save()

            msg = '{} \n {} {}'.format(
                'Links added to ->' + string,
                'Created' if not form.instance.pk else 'Modified',
                self.model._meta.verbose_name,
            )
            logger.info(f"{msg} {obj} (PK: {obj.pk})")
            if hasattr(obj, 'get_absolute_url'):
                msg = '{} <a href="{}">{}</a>'.format(
                    msg, obj.get_absolute_url(), escape(obj))
            else:
                msg = '{} {}'.format(msg, escape(obj))
            messages.success(request, mark_safe(msg))

            if '_addanother' in request.POST:

                # If the object has clone_fields, pre-populate a new instance of the form
                if hasattr(obj, 'clone_fields'):
                    url = '{}?{}'.format(
                        request.path, prepare_cloned_fields(obj))
                    return redirect(url)

                return redirect(request.get_full_path())

            return_url = form.cleaned_data.get('return_url')
            if return_url is not None and is_safe_url(url=return_url, allowed_hosts=request.get_host()):
                return redirect(return_url)
            else:
                return redirect(self.get_return_url(request, obj))

        else:
            logger.debug("Form validation failed")

        return render(request, self.template_name, {
            'obj': self.obj,
            'obj_type': self.model._meta.verbose_name,
            'form': form,
            'return_url': self.get_return_url(request, self.obj),
        })


class PaymentListView(View, PermissionRequiredMixin):
    permission_required = 'payment.view_payment'
    queryset = Payment.objects.all()
    filterset = filters.PaymentFilterSet
    filterset_form = forms.PaymentFilterForm
    table = tables.PaymentTable
    template_name = 'payment/obj_list.html'
    action_buttons = ('export')
    form = forms.ReportForm

    def queryset_to_csv(self):
        """
        Export the queryset of objects as comma-separated value (CSV), using the model's to_csv() method.
        """
        csv_data = []
        custom_fields = []

        # Start with the column headers
        headers = self.queryset.model.csv_headers.copy()

        # Add custom field headers, if any
        if hasattr(self.queryset.model, 'get_custom_fields'):
            for custom_field in self.queryset.model().get_custom_fields():
                headers.append(custom_field.name)
                custom_fields.append(custom_field.name)

        csv_data.append(','.join(headers))

        # Iterate through the queryset appending each object
        for obj in self.queryset:
            data = obj.to_csv()

            for custom_field in custom_fields:
                data += (obj.cf.get(custom_field, ''),)

            csv_data.append(csv_format(data))

        return '\n'.join(csv_data)

    def get(self, request):

        model = self.queryset.model
        content_type = ContentType.objects.get_for_model(model)

        if self.filterset:
            self.queryset = self.filterset(request.GET, self.queryset).qs

        # If this type of object has one or more custom fields, prefetch any relevant custom field values
        custom_fields = CustomField.objects.filter(
            obj_type=ContentType.objects.get_for_model(model)
        ).prefetch_related('choices')
        if custom_fields:
            self.queryset = self.queryset.prefetch_related(
                'custom_field_values')

        # Check for export template rendering
        if request.GET.get('export'):
            et = get_object_or_404(
                ExportTemplate, content_type=content_type, name=request.GET.get('export'))
            queryset = CustomFieldQueryset(
                self.queryset, custom_fields) if custom_fields else self.queryset
            try:
                return et.render_to_response(queryset)
            except Exception as e:
                messages.error(
                    request,
                    "There was an error rendering the selected export template ({}): {}".format(
                        et.name, e
                    )
                )

        # Check for YAML export support
        elif 'export' in request.GET and hasattr(model, 'to_yaml'):
            response = HttpResponse(
                self.queryset_to_yaml(), content_type='text/yaml')
            filename = 'netbox_{}.yaml'.format(
                self.queryset.model._meta.verbose_name_plural)
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(
                filename)
            return response

        # Fall back to built-in CSV formatting if export requested but no template specified
        elif 'export' in request.GET and hasattr(model, 'to_csv'):
            response = HttpResponse(
                self.queryset_to_csv(), content_type='text/csv')
            filename = 'netbox_{}.csv'.format(
                self.queryset.model._meta.verbose_name_plural)
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(
                filename)
            return response

        # Provide a hook to tweak the queryset based on the request immediately prior to rendering the object list
        self.queryset = self.alter_queryset(request)

        # Compile a dictionary indicating which permissions are available to the current user for this model
        permissions = {}
        for action in ('add', 'change', 'delete', 'view'):
            perm_name = '{}.{}_{}'.format(
                model._meta.app_label, action, model._meta.model_name)
            permissions[action] = request.user.has_perm(perm_name)

        # Construct the table based on the user's permissions
        table = self.table(self.queryset)
        if 'pk' in table.base_columns and (permissions['change'] or permissions['delete']):
            table.columns.show('pk')

        # Apply the request context
        paginate = {
            'paginator_class': EnhancedPaginator,
            'per_page': request.GET.get('per_page', settings.PAGINATE_COUNT)
        }
        RequestConfig(request, paginate).configure(table)

        context = {
            'content_type': content_type,
            'table': table,
            'permissions': permissions,
            'action_buttons': self.action_buttons,
            'filter_form': self.filterset_form(request.GET, label_suffix='') if self.filterset_form else None,
            'form': self.form,
        }
        context.update(self.extra_context())

        return render(request, self.template_name, context)

    def alter_queryset(self, request):
        # .all() is necessary to avoid caching queries
        return self.queryset.all()

    def extra_context(self):
        return {}


class PaymentView(View, PermissionRequiredMixin):
    permission_required = 'payment.view_payment'

    def get(self, request, slug):
        model = Payment

        permissions = {}
        for action in ('add', 'change', 'delete', 'view'):
            perm_name = '{}.{}_{}'.format(
                model._meta.app_label, action, model._meta.model_name)
            permissions[action] = request.user.has_perm(perm_name)

        payment = get_object_or_404(Payment.objects.filter(slug=slug))
        return render(request, 'payment/pay.html', {
            'payment': payment,
            'permissions': permissions
        })


class PaymentCreateView (PaymentCreate, PermissionRequiredMixin):
    permission_required = 'payment.add_payment'
    model = Payment
    model_form = forms.PaymentForm
    default_return_url = 'plugins:payment:payment_list'


class PaymentEditView(PaymentCreateView):
    permission_required = 'payment.change_payment'


class PaymentDeleteView(PaymentDeleteView):
    model = Payment
    default_return_url = 'plugins:payment:payment_list'


class ContractAttachementEditView(ObjectEditView):
    model = ContractFile
    model_form = forms.ContractAttachmentForm

    def alter_obj(self, contractfile, request, args, kwargs):
        if not contractfile.pk:
            model = kwargs.get('model')
            contractfile.parent = get_object_or_404(
                model, pk=kwargs['object_id'])
        return contractfile

    def get_return_url(self, request, contractfile):
        return contractfile.parent.get_absolute_url()


class ContractDeleteView(ObjectDeleteView):
    model = ContractFile

    def get_return_url(self, request, contractfile):
        return contractfile.parent.get_absolute_url()


class ReportView(View, PermissionRequiredMixin):
    permission_required = 'payment.view_payment'
    queryset = Payment.objects.all()

    def to_table(self, period):

        csv_data = []

        headers = self.queryset.model.csv_headers.copy()
        csv_data.append(','.join(headers))
        for obj in Payment.objects.all():
            if period == 'Годовой':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(format_in_csv(data))
                elif obj.period == 'yearly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Январь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 1:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Февраль':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 2:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Март':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 3:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Апрель':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 4:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Май':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 5:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Июнь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 6:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Июль':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 7:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Август':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 8:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Сентябрь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 9:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Октябрь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 10:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Ноябрь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 11:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
            elif period == 'Декабрь':
                if obj.period == 'monthly':
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))
                elif obj.period == 'yearly' and obj.payment_date.month == 12:
                    data = obj.to_csv()
                    csv_data.append(csv_format(data))

        return '\n'.join(csv_data)

    def post(self, request, *args, **kwargs):
        data = forms.ReportForm(request.POST or None)
        if request.method == "POST" and data.is_valid():
            value = data.cleaned_data['date']
        response = HttpResponse(self.to_table(value), content_type='text/csv')
        filename = 'netbox_{}.csv'.format(
            self.queryset.model._meta.verbose_name_plural)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            filename)
        return response


def format_in_csv(data):
    """
    Encapsulate any data which contains a comma within double quotes.
    """
    csv = []
    arg_list = list(data)
    arg_list[3] = '=' + str(arg_list[3]) + '*12'
    for value in arg_list:

        # Represent None or False with empty string
        if value is None or value is False:
            csv.append('')
            continue

        # Convert dates to ISO format
        if isinstance(value, (datetime.date, datetime.datetime)):
            value = value.isoformat()

        # Force conversion to string first so we can check for any commas
        if not isinstance(value, str):
            value = '{}'.format(value)

        # Double-quote the value if it contains a comma or line break
        if ',' in value or '\n' in value:
            value = value.replace('"', '""')  # Escape double-quotes
            csv.append('"{}"'.format(value))
        else:
            csv.append('{}'.format(value))

    return ','.join(csv)
