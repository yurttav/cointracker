from django import forms
from .models import BinanceCoinList

class CoinListForm(forms.ModelForm):
    #form oluşturmada kolay metot, class göre model oluşturma, detaylar için internet modelform django
    class Meta:
        model = BinanceCoinList
        fields = ["coinsymbol","trackstate"]
  