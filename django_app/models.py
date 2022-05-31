from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MaxValueValidator
import base58


class Transaction(models.Model):
    Id = models.CharField(max_length=100)
    Description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'ID: {self.Id}\nDescription: {self.Description}'

    def get_url(self):
        return reverse('tx-detail', args=(self.Id, ))


class TransactionData:
    RPC_URL = r'http://bcs_tester:iLoveBCS@45.32.232.25:3669'
    PUB_KEY = 'BQWh2DNBi9vcfqToBrUPUwPXppwmajJYv9'
    UTXO_ADDRESS = r'https://bcschain.info/api/address/{}/utxo'.format(PUB_KEY)
    PRIV_KEY = base58.b58encode(b'L5D4e2m4KJqF8uPq99MfRDZhYf6UKDbr4ezfeXfxdPYewiHQeGfA')


class RpcException(Exception):
    pass