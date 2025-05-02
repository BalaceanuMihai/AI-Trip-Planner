from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_ui, name='chat_ui'),
    path('api/', views.chat_api, name='chat_api'),
    path('select/', views.select_destination, name='select_destination'),
    path('end/', views.end_conversation, name='end_conversation'),
]
