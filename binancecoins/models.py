from django.db import models

# Create your models here.

class BinanceCoinList(models.Model):
    coinsymbol = models.CharField(max_length = 10, verbose_name = "Coin", primary_key=True)
    trackstate = models.BooleanField(verbose_name="Takip Durumu")
    
    def __str__(self):
        return self.coinsymbol
    
    class Meta:
        ordering = ['coinsymbol'] #- ile son girilen makalenin ilk gösterilmesi sağlanıyor