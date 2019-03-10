from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

import requests
from datetime import datetime, timedelta
from .models import BinanceCoinList

# Create your views here.
"""
def removecoinfromlist(allcoins):
    newallcoins = []
    binance_all_symbols.clear()

    for i in allcoins:
        if i['symbol'].find("BTC") != -1:
            newallcoins.append(i)
            binance_all_symbols.append(i['symbol'])
    return newallcoins
"""

def filtercoins(allcoins):
    newallcoins = []

    for i in allcoins:
        coin = BinanceCoinList.objects.filter(coinsymbol = i['symbol'], trackstate=True)
        if coin:
            newallcoins.append(i)
    return newallcoins

def maketableforweb(coindata):
    newcoindata = []
    for i in coindata:
        x = []
        coindate = datetime.fromtimestamp(i[6]/ 1000)
        x.append(coindate.strftime('%Y.%m.%d %H:%M'))
        x.append(i[2])
        x.append(i[3])
        x.append(i[4])
        x.append(str((float(i[2])-float(i[3]))/float(i[3])*100)[:4])
        x.append(str(i[7])[:6])
        x.append(str(i[10])[:6])
        x.append(str(float(i[7])-float(i[10]))[:6])
        if float(i[7]) == 0:
            x.append("0")
        else:
            x.append(str(float(i[10])/float(i[7])*100)[:4])
        x.append(False)
        x.append(False)
        x.append(False)
        x.append(False)
        newcoindata.append(x)
    newcoindata.reverse()
    return newcoindata

def MACalc(binanceallcoins,days):
        maval = 0.0
        if len(binanceallcoins) < days:
            return 0.0

        for i in range(days):
            maval += float(binanceallcoins[i][3])
        return maval/days
    
def index(request):
    url = "https://api.binance.com/api/v1/ticker/24hr"
    response = requests.get(url)
    binanceallcoins = response.json()
    binanceallcoins = filtercoins(binanceallcoins)
    context = {
        "binanceallcoins":binanceallcoins,
    }
    return render(request, "index.html",context)

def arsiv(request):

    selected_coin = request.GET.get("selected_coin")
    binanceallcoins = []
    binance_all_symbols = BinanceCoinList.objects.filter(trackstate = True)
    context = dict()
    start_time = datetime.strftime(datetime.now() - timedelta(days=15), '%d.%m.%Y %H:%M')
    end_time = datetime.strftime(datetime.now(), '%d.%m.%Y %H:%M')

    if BinanceCoinList.objects.filter(coinsymbol = selected_coin):
        limit = request.GET.get("data_count")
        if not(limit):
        #hata kontrolü eklenmesi lazım
            limit = "1000"
        elif int(limit) > 1000:
            limit = "1000"
        interval = request.GET.get("timeinterval")    
        if not(interval):
            interval = "1d" 
        Checkboxischecked = request.GET.get("checkboxstate")

        if not(Checkboxischecked):
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit={}".format(selected_coin, interval, limit)
        else:
            start_time = datetime.strptime(request.GET.get("datetimepicker1"), '%d.%m.%Y %H:%M')
            end_time = datetime.strptime(request.GET.get("datetimepicker2"), '%d.%m.%Y %H:%M')
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&startTime={}&endTime={}&limit={}".format(selected_coin, interval, int(datetime.timestamp(start_time)*1000), int(datetime.timestamp(end_time)*1000), limit)
            start_time = datetime.strftime(start_time, '%d.%m.%Y %H:%M')
            end_time = datetime.strftime(end_time, '%d.%m.%Y %H:%M')
        response = requests.get(url)
        binanceallcoins = response.json()
        binanceallcoins = maketableforweb(binanceallcoins)
        context = {
        "selected_coin":selected_coin,
        "interval":interval,
        "limit":limit, 
        }
        print(interval)

        voltable = []
        maxvalrow = 0
        minvalrow = 0
        maxval = float(binanceallcoins[0][1])
        minval = float(binanceallcoins[0][2])

        for index in range(len(binanceallcoins)):

            if float(binanceallcoins[index][1]) >= maxval:
                maxval = float(binanceallcoins[index][1])
                maxvalrow = index

            if float(binanceallcoins[index][2])<=minval:
                minval = float(binanceallcoins[index][2])
                minvalrow = index

            vol1 = float(binanceallcoins[index][5])
            if index+1 < len(binanceallcoins):
                vol2 = float(binanceallcoins[index+1][5])
            else:
                vol2 = vol1
            istotalvoladded = False

            volxtable = []

            if vol1 != 0:
                if ((vol1-vol2)/vol1 >= 0.9) and vol1 >= 2:
                    volxtable.append(binanceallcoins[index][0])
                    volxtable.append(binanceallcoins[index][5])
                    volxtable.append(binanceallcoins[index][6])
                    volxtable.append(binanceallcoins[index][3])
                    voltable.append(volxtable)
                    binanceallcoins[index][9] = True
            
            volxtable = []

            vol1 = float(binanceallcoins[index][6])
            if index+1 < len(binanceallcoins):
                vol2 = float(binanceallcoins[index+1][6])
            else:
                vol2 = vol1
            
            if vol1 != 0:
                if ((vol1-vol2)/vol1 >= 0.9) and vol1 >= 2:
                    if not(istotalvoladded):
                        volxtable.append(binanceallcoins[index][0])
                        volxtable.append(binanceallcoins[index][5])
                        volxtable.append(binanceallcoins[index][6])
                        volxtable.append(binanceallcoins[index][3])
                        voltable.append(volxtable)
                        binanceallcoins[index][10] = True
        minmaxlist = []
        minmaxlist.append(binanceallcoins[maxvalrow][1])
        minmaxlist.append(binanceallcoins[maxvalrow][0])
        minmaxlist.append(binanceallcoins[minvalrow][2])
        minmaxlist.append(binanceallcoins[minvalrow][0])
        minmaxlist.append(binanceallcoins[0][3])
        lastval = float(binanceallcoins[0][3])
        minmaxlist.append(str(100 * (lastval - maxval) / maxval)[:5])
        minmaxlist.append(str((lastval - minval) / minval * 100)[:5])

        ma7 = MACalc(binanceallcoins,7)
        ma25 = MACalc(binanceallcoins,25)
        ma99 = MACalc(binanceallcoins,99)

        context["minmaxlist"] = minmaxlist
        context["voltable"] = voltable
        binanceallcoins[maxvalrow][11] = True
        binanceallcoins[minvalrow][12] = True
        #context["maxvalrow"] = maxvalrow
        #context["minvalrow"] = minvalrow

        matable = []
        matablerow = []
        matablerow.append("{:.8f}".format(ma7))
        matablerow.append("{:.8f}".format(ma25))
        matablerow.append("{:.8f}".format(ma99))
        matable.append(matablerow)
        matablerow = []
        if ma7 != 0 and ma25 != 0:
            matablerow.append("%{:.2f}".format((ma7-ma25)/ma7*100))
        else:
            matablerow.append("N/A")

        if ma25 != 0 and ma99 != 0:
            matablerow.append("%{:.2f}".format((ma25-ma99)/ma25*100))
        else:
            matablerow.append("N/A")
        matablerow.append("N/A")
        matable.append(matablerow)
        context["matable"] = matable

    context["binanceallcoins"] = binanceallcoins
    context["binance_all_symbols"] = binance_all_symbols
    print(start_time)
    context["start_time"] = start_time
    context["end_time"] = end_time

    return render(request, "arsiv.html",context)#content sözlük olarak verilmesi lazım

def about(request):
    return render(request, "about.html")

def test(request):
    
    url = "https://api.binance.com/api/v1/ticker/24hr"
    response = requests.get(url)
    binanceallcoins = response.json()
    binanceallcoins = filtercoins(binanceallcoins)
    context = {
        "binanceallcoins":binanceallcoins,
    }
    return render(request, "test.html", context)

def coinlist(request):
    url = "https://api.binance.com/api/v1/ticker/24hr"
    response = requests.get(url)
    binanceallcoins = response.json()
    for i in binanceallcoins:
        coin = BinanceCoinList.objects.filter(coinsymbol = i['symbol'])
        if not(coin):
            if i['symbol'].find("BTC") != -1:
                newcoin = BinanceCoinList(coinsymbol = i['symbol'], trackstate = True)
            else:
                newcoin = BinanceCoinList(coinsymbol = i['symbol'], trackstate = False)
            newcoin.save()

    keyword = request.GET.get("keyword")
    if keyword:
        binanceallcoins =  BinanceCoinList.objects.filter(coinsymbol__contains = keyword)
    else:
        binanceallcoins =  BinanceCoinList.objects.all()

    context = {
        "binanceallcoins":binanceallcoins
    }
    return render(request, "coinlist.html", context)

def deleteallcoin(request):
    
    binanceallcoins =  BinanceCoinList.objects.all()
    binanceallcoins.delete()

    messages.success(request,"Başarıyla silindi...")

    return redirect("coinlist")

#    return render(request, "coinlist.html", context)

def update(request, id):
    coin = get_object_or_404(BinanceCoinList, coinsymbol = id)
    coin.trackstate = not(coin.trackstate)
    coin.save()

    return redirect("coinlist")

def minmax(request):

    minmaxtable = []

    if request.GET.get("datetimepicker1"):
        start_time = datetime.strptime(request.GET.get("datetimepicker1"), '%d.%m.%Y %H:%M')
        end_time = datetime.strptime(request.GET.get("datetimepicker2"), '%d.%m.%Y %H:%M')
        if start_time == end_time:
            return 
        
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url)
        binanceallcoins = response.json()
        binanceallcoins = filtercoins(binanceallcoins)

        limit = "1000"
        interval = "1d"
                
        for x in binanceallcoins:
            minmaxtablerow = []
            symbol = x['symbol']
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&startTime={}&endTime={}&limit={}".format(
                symbol, interval, int(datetime.timestamp(start_time) * 1000),
                int(datetime.timestamp(end_time) * 1000), limit)
            response = requests.get(url)
            binanceallcoins2 = response.json()
                
            if len(binanceallcoins2) == 0:
                continue

            maxval = float(binanceallcoins2[0][2])
            minval = float(binanceallcoins2[0][3])
            maxvaldate = start_time
            minvaldate = start_time

            for i in binanceallcoins2:
                if float(i[2]) >= maxval:
                    maxval = float(i[2])
                    maxvaldate = datetime.fromtimestamp(i[6] / 1000)
                if float(i[3]) <= minval:
                    minval = float(i[3])
                    minvaldate = datetime.fromtimestamp(i[6] / 1000)

            minmaxtablerow.append(symbol)
            minmaxtablerow.append(x['price'])
            minmaxtablerow.append("{:.8f}".format(maxval))
            minmaxtablerow.append(maxvaldate.strftime('%Y.%m.%d %H:%M'))
            minmaxtablerow.append("{:06.2f}".format(100 * (float(x['price']) - maxval) / maxval))
            minmaxtablerow.append("{:.8f}".format(minval))
            minmaxtablerow.append(minvaldate.strftime('%Y.%m.%d %H:%M'))
            minmaxtablerow.append("{:06.2f}".format((float(x['price']) - minval) / minval * 100))
            minmaxtable.append(minmaxtablerow)
        start_time = datetime.strftime(start_time, '%d.%m.%Y %H:%M')
        end_time = datetime.strftime(end_time, '%d.%m.%Y %H:%M')
    else:
        start_time = datetime.strftime(datetime.now() - timedelta(days=15), '%d.%m.%Y %H:%M')
        end_time = datetime.strftime(datetime.now(), '%d.%m.%Y %H:%M')

    context = {
        "binanceallcoins":minmaxtable,
        "start_time" : start_time,
        "end_time" : end_time,
    }
    return render(request, "minmax.html", context)