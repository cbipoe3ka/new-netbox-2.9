import django_filters
from django.db.models import Q

from dcim.models import Region, Site
from extras.filters import CustomFieldFilterSet, CreatedUpdatedFilterSet
from tenancy.filters import TenancyFilterSet
from utilities.filters import (
    BaseFilterSet, NameSlugSearchFilterSet, TagFilter, TreeNodeMultipleChoiceFilter
)
from .choices import *
from .models import Payment


__all__ = (
    'PaymentFilterSet'
)

class PaymentFilterSet(BaseFilterSet):
    
    q = django_filters.CharFilter(
        method = 'search',
        label = 'Search'
    )

    payment_type = django_filters.MultipleChoiceFilter(
         choices = PaymentTypeChoices,
         null_value = None
     )
     
    period = django_filters.MultipleChoiceFilter(
        choices = PaymentPeriodChoices,
        null_value=None
    ) 
    class Meta:
         model = Payment
         fields = ['name', 'price', 'payment_type']
    
    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(payment_type__icontains=value) |
            Q(period__icontains=value)
            ).distinct()