import django_tables2 as tables
from django_tables2.utils import Accessor

from tenancy.tables import COL_TENANT
from utilities.tables import BaseTable, ToggleColumn

from .models import Payment



PAYMENT_ACTIONS = """
{% if perms.payment.change_payment %}
<a href="{% url 'plugins:payment:payment_edit' pk=record.pk %}" 
  class="btn btn-xs btn-warning"><i class="glyphicon glyphicon-pencil" aria-hidden="true"></i></a>
{% endif %}
{% if perms.payment.add_payment %}
<a href= "{% url 'plugins:payment:payment_delete' pk=record.pk %}"
 class="btn btn-xs btn-danger"><i class="glyphicon glyphicon-remove" aria-hidden="true"></i></a>
{% endif %}

"""


class PaymentTable(BaseTable):
    pk = ToggleColumn()

    name = tables.LinkColumn()


    actions = tables.TemplateColumn (
        template_code=PAYMENT_ACTIONS,
        attrs={'td': {'class': 'text-right noprint'}},
        verbose_name=''
    )


    class Meta(BaseTable.Meta):
        model = Payment
        fields = ('pk', 'name', 'payment_type', 'period', 'price', 'currency', 'contractor', 'actions')