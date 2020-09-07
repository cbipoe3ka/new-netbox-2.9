import re
from django import forms
from utilities import forms as F
from .models import Payment, ContractFile, Contractor, Report
from tenancy.forms import TenancyFilterForm, TenancyForm
from tenancy.models import Tenant
from extras.forms import (
    AddRemoveTagsForm, CustomFieldBulkEditForm, CustomFieldFilterForm, CustomFieldModelForm, CustomFieldModelCSVForm,
)
from utilities.forms import (
    APISelect, APISelectMultiple, add_blank_choice, BootstrapMixin, CommentField, CSVChoiceField, DatePicker,
    DynamicModelChoiceField, DynamicModelMultipleChoiceField, SmallTextarea, SlugField, StaticSelect2,
    StaticSelect2Multiple, TagFilterField,
)
from taggit.forms import TagField
from .choices import PaymentPeriodChoices, PaymentTypeChoices, ReportChoices
import django_filters



class PaymentForm(F.BootstrapMixin, forms.ModelForm):
 #   name = F.SmallTextarea()
 #   price = F.SmallTextarea()
 #   payment_date = F.DatePicker()
 #   devices = F.StaticSelect2Multiple

    slug = SlugField()
    comments = CommentField()

    


    class Meta:
        model = Payment

        

        fields = [
            'name', 'work_description', 'sub_project', 'price', 'currency', 'comp', 'contractor', 'payment_date', 'period','payment_type', 'devices', 'circuits', 'comments', 'slug',
        ]
        widgets = {
            'sub_project' : F.StaticSelect2(),
            'comp': F.StaticSelect2(),
            'currency' : F.StaticSelect2(),
            'contractor' : F.StaticSelect2(),
            'payment_date' : F.DatePicker(),
            'devices' : F.StaticSelect2Multiple(),
            'circuits': F.StaticSelect2Multiple(),
            'period' : F.StaticSelect2(),
            'payment_type' : F.StaticSelect2(),
        }

class ContractAttachmentForm(F.BootstrapMixin, forms.ModelForm):

    class Meta:
        model = ContractFile
        fields = [
            'name', 'document',
        ]

class PaymentFilterForm (BootstrapMixin, CustomFieldFilterForm, forms.Form):
    model = Payment

    q = forms.CharField(
        required=False,
        label='Search'
    )

    period = forms.MultipleChoiceField (
        choices=PaymentPeriodChoices,
        required=False,
        widget=StaticSelect2Multiple
    )



    payment_type = forms.MultipleChoiceField (
        choices= PaymentTypeChoices,
        required=False,
        widget=StaticSelect2Multiple
    )

class ReportForm(F.BootstrapMixin, forms.ModelForm):


    class Meta:
        model = Report

        fields = ['date']

        widgets = {
            'date' : F.StaticSelect2(),
        }
    





