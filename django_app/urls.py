from django.urls import path
from .views import *

urlpatterns = [
    path('', show_all_txs),
    path('tx/<str:txid>', show_tx, name='tx-detail'),
    path('sendtx/', send, name='send-tx')
]