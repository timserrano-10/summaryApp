from django.urls import path
from . import views

urlpatterns = [
    # routes to the upload_document function in view
    path('', views.upload_document, name='upload_document'),
    # routes to the document detail function inside view
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
]