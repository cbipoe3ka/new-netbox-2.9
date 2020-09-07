from django.urls import path

from . import views
from .models import Payment, ContractFile

app_name = 'payment'


urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment_list'),  
    path('add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('report/', views.ReportView.as_view(), name='report'),
    path('<slug:slug>/', views.PaymentView.as_view(), name='payment_view'),
    path('<int:pk>/edit/', views.PaymentEditView.as_view(), name='payment_edit'),
    path('<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    path('<int:object_id>/add/contract', views.ContractAttachementEditView.as_view(), name='contract_add', kwargs={'model': Payment}),
    path('<int:pk>/delete/contract', views.ContractDeleteView.as_view(), name='contract_delete', kwargs={'model': ContractFile }),

  
]
