from django.db import models
from dcim.models import Device
from circuits.models import Circuit
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.urls import reverse
from .choices import PaymentPeriodChoices, PaymentTypeChoices, CurrencyChoices, SubProjectChoices, ReportChoices

# Create your models here.
__all__ = (
    'ContractFile',
    'Payment',
)


class ContractFile(models.Model):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey(
        ct_field='content_type',
        fk_field='object_id'
    )

    name = models.CharField(
        max_length=30,
        verbose_name='File name'
    )

    document = models.FileField (
        upload_to='devicetype-images'
    )

    created = models.DateTimeField (
        auto_now_add=True
    )

    def __str__(self):
        return self.name
    
        

    class Meta:
        ordering = ['name']


class Contractor(models.Model):
    name = models.CharField(
        max_length=70,
        verbose_name='Контрагент'
    )

    description = models.TextField(
        verbose_name='Описание контрагента'
    )

    def __str__(self):
        return self.name


    class Meta:
        ordering = ['name']

class Company(models.Model):
    name = models.CharField(
        max_length=70,
        verbose_name='Компания плательщик'
    )

    description = models.TextField(
        verbose_name='Описание компании'
    ) 
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Report(models.Model):
    date = models.CharField(
        max_length=70,
        verbose_name='Год\Месяц',
        choices=ReportChoices,
        default=ReportChoices.YEAR
    )

    def __str__(self):
        return self.date


    
class Payment(models.Model):
    name = models.CharField(
        max_length=70,
        verbose_name='Название'
    )

    work_description = models.CharField(
        max_length=150,
        verbose_name='Назначение платежа',
        default=' '
    )

    sub_project = models.CharField(
        max_length=70,
        choices=SubProjectChoices,
        default=SubProjectChoices.STUDIO,
        blank=True,
        verbose_name='Подпроект'
    )


    slug = models.SlugField(
        unique=True
    )

    price = models.IntegerField(
        verbose_name='Стоимость'
    )

    currency = models.CharField(
        max_length=10,
        choices=CurrencyChoices,
        default=CurrencyChoices.DOLLAR,
        verbose_name='Валюта'
    )

    comp = models.ForeignKey(
        to=Company,
        on_delete=models.PROTECT,
        verbose_name = 'Компания плательщик'
    )


    contractor = models.ForeignKey(
        to=Contractor,
        on_delete=models.PROTECT,
        verbose_name='Контрагент'
    )

    period = models.CharField(
        max_length=50,
        choices=PaymentPeriodChoices,
        default=PaymentPeriodChoices.PAYMENT_MONTH,
        verbose_name='Период'
    )

    payment_type = models.CharField(
        max_length=50,
        choices=PaymentTypeChoices,
        default=PaymentTypeChoices.TYPE_RENT,
        verbose_name='Тип платежа'
    )


    payment_date = models.DateField (
        verbose_name='Дата оплаты',
        auto_now=False,
        auto_now_add=False
    )

    devices = models.ManyToManyField(
        to=Device,
        blank=True,
    )

    circuits = models.ManyToManyField(
        to=Circuit,
        blank=True,
    )

    contract = GenericRelation (
        to='ContractFile'
    )


    comments = models.TextField (
        blank=True
    )
    csv_headers = ['Контрагент', 'Компания плательщик', 'Назначение платежа', 'Сумма платежа', 'Валюта', 'Дата оплаты', 'Периодичность', 'Подпроект', 'Подготовил', 'Ответственный', 'Комментарий']

   
    class Meta:
        ordering = ['payment_date', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:payment:payment_view', args=[self.slug])

    def to_csv(self): 
        blank_value=''
    

        return (
            self.contractor,
            self.comp,
            self.work_description,
            self.price,
            self.currency,
            self.payment_date,
            self.period,
            self.sub_project,
            blank_value,
            blank_value,
            blank_value
        )
