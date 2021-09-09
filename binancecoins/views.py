from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib import messages

import requests, json
from datetime import datetime, timedelta
from .models import BinanceCoinList

from bs4 import BeautifulSoup
import urllib3


# Create your views here.

ma_table = []

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
    #newcoindata.sort(reverse = True)
    newcoindata.reverse()
    #print(newcoindata)
    return newcoindata

def MACalc(binanceallcoins,days,arrayindex):
    if len(binanceallcoins) < days:
        return 0.0
    if days <= 0:
        return 0.0
    maval = 0.0
    for i in range(days):
        maval += float(binanceallcoins[i][arrayindex])
    return maval/days

def WMACalc(binanceallcoins,days,arrayindex):
    if len(binanceallcoins) < days:
        return 0.0
    if days <= 0:
        return 0.0
    maval = 0.0
    factordays = 0
    for i in range(days):
        maval += float(binanceallcoins[i][arrayindex]) * (days-i)
        factordays += days-i
    return maval/factordays

def index(request):
    url = "https://api.binance.com/api/v1/ticker/24hr"
    response = requests.get(url)
    binanceallcoins = response.json()
    binanceallcoins = filtercoins(binanceallcoins)
    context = {
        "binanceallcoins":binanceallcoins,
    }
    return render(request, "index.html",context)

def calcRSI(binanceallcoins, arrayindex):
    RSI = 0
    if len(binanceallcoins) < 15:
        return RSI
    positives = 0
    negatives = 0
    binanceallcoins.sort()
    for i in range(1,15):
        delta = float(binanceallcoins[i][arrayindex]) - float(binanceallcoins[i-1][arrayindex])
        #print(i," : ","{:.8f}".format(delta))
        if delta >= 0:
            positives += delta
        else:
            negatives += abs(delta)
    positives /= 14
    negatives /= 14
    for i in range(15,len(binanceallcoins)):
        delta = float(binanceallcoins[i][arrayindex]) - float(binanceallcoins[i-1][arrayindex])
        if delta >= 0:
            positives = (positives*13+delta)/14
            negatives = (negatives*13)/14
        else:
            positives = (positives*13)/14
            negatives = (negatives*13+abs(delta))/14
        if negatives != 0:
            rs = positives / negatives
            RSI = 100-(100/(1+rs))
        else:
            RSI = 0
        #print(i," positives : ","{:.8f}".format(positives)," negatives : ", "{:.8f}".format(negatives)," RS : ", "{:.8f}".format(rs), " RSI : ", "{:.8f}".format(RSI))
    """
    positives /= 14
    negatives /= 14
    delta = float(binanceallcoins[0][arrayindex]) - float(binanceallcoins[1][arrayindex])
    if delta > 0:
        rs = ((positives*13 + delta)/14) / ((negatives*13 + 0         )/14)
    else:
        rs = ((positives*13 + 0    )/14) / ((negatives*13 + abs(delta))/14)
    print(positives," : ",negatives," : ", rs, " : ", 100-(100/(1+rs)))
    return 100-(100/(1+rs))
    """
    return RSI

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
            #print("cb çek edilmedi")
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit={}".format(selected_coin, interval, limit)
        else:
            #print("cb çek")

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
                    istotalvoladded = True

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

        ma7 = MACalc(binanceallcoins,7,3)
        ma25 = MACalc(binanceallcoins,25,3)
        ma99 = MACalc(binanceallcoins,99,3)
        wma50 = WMACalc(binanceallcoins,50,3)
        RSI = calcRSI(binanceallcoins,3)

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
        matablerow.append("{:.8f}".format(wma50))
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
        #matablerow.append("N/A")
        matablerow.append("{:.8f}".format(RSI))

        matable.append(matablerow)
        context["matable"] = matable

    context["binanceallcoins"] = binanceallcoins
    context["binance_all_symbols"] = binance_all_symbols
    context["start_time"] = start_time
    context["end_time"] = end_time

    return render(request, "arsiv.html",context)#content sözlük olarak verilmesi lazım

def about(request):
    showprogress("25")
    return render(request, "about.html")
    #return HttpResponse("deneme")

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
            if (i['symbol'].find("BTC") != -1) or (i['symbol'].find("USDT") != -1):
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
    interval = request.GET.get("timeinterval")

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
        if not(interval):
            interval = "1d"

        for x in binanceallcoins:
            minmaxtablerow = []
            symbol = x['symbol']
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&startTime={}&endTime={}&limit={}".format(
                symbol, interval, int(datetime.timestamp(start_time) * 1000),
                int(datetime.timestamp(end_time) * 1000), limit)
            response = requests.get(url)
            binanceallcoins2 = response.json()
            binanceallcoins2.sort(key=lambda x:x[0], reverse = True)

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
            ma7 = MACalc(binanceallcoins2,7,4)
            ma25 = MACalc(binanceallcoins2,25,4)
            ma99 = MACalc(binanceallcoins2,99,4)
            minmaxtablerow.append("{:.8f}".format(ma7))
            minmaxtablerow.append("{:.8f}".format(ma25))
            minmaxtablerow.append("{:.8f}".format(ma99))
            minmaxtablerow.append("{:06.2f}".format((maxval - minval) / minval * 100))
            urlvol = "https://api.binance.com/api/v1/ticker/24hr?symbol={}".format(symbol)
            response = requests.get(urlvol)
            volofsymbol = response.json()
            minmaxtablerow.append("{:.2f}".format(float(volofsymbol['quoteVolume'])))
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
        "interval" : interval
    }
    return render(request, "minmax.html", context)

def pricecompare(price,maval,isabs):
    if price != 0:
        if isabs:
            return "{:06.2f}".format(abs(100 * (price - maval) / price))
        else:
            return "{:06.2f}".format(100 * (price - maval) / price)
    else:
        return "N/A"

def showprogress(progress):
    return HttpResponse(progress)

def filter_ma99_25(state):
    global ma_table
    if state:
        for x in ma_table:
            x[9] = True
    else:
        for x in ma_table:
            if (float(x[1]) > float(x[4])) and (float(x[1]) < float(x[6])):
                x[9] = True
            else:
                x[9] = False
    return

def filter_wma50(greater):
    global ma_table
    if greater:
        for x in ma_table:
            if float(x[11]) < 2 and float(x[11]) > 0 :
                x[9] = True
            else:
                x[9] = False
    else:
        for x in ma_table:
            if float(x[11]) > -2 and float(x[11]) < 0 :
                x[9] = True
            else:
                x[9] = False
    return

def madurum(request):
    global ma_table
    Checkboxischecked1 = request.GET.get("checkboxstate1")
    Checkboxischecked2 = request.GET.get("checkboxstate2")
    Checkboxischecked3 = request.GET.get("checkboxstate3")
    Checkboxischecked4 = request.GET.get("checkboxstate4")

    interval = request.GET.get("timeinterval")

    if Checkboxischecked1:
        if ma_table == []:
            return render(request, "madurum.html")
        else:
            filter_ma99_25(False)
    elif Checkboxischecked2:
        filter_ma99_25(True)
    elif Checkboxischecked3:
        filter_wma50(True)
    elif Checkboxischecked4:
        filter_wma50(False)
    elif request.GET.get("timeinterval"):
    #if request.method == "POST":
        ma_table = []
        url = "https://api.binance.com/api/v3/ticker/price"
        response = requests.get(url)
        binanceallcoins = response.json()
        binanceallcoins = filtercoins(binanceallcoins)

        limit = "1000"
        interval = request.GET.get("timeinterval")
        #interval = "1d"

        #totalprogress = len(binanceallcoins)
        #currentprogress = 0

        for x in binanceallcoins:
            ma_tablerow = []
            symbol = x['symbol']
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&limit={}".format(
                symbol, interval, limit)
            response = requests.get(url)
            binanceallcoins2 = response.json()
            binanceallcoins2.sort(key=lambda x:x[0], reverse = True)

            if len(binanceallcoins2) == 0:
                continue

            ma7 = MACalc(binanceallcoins2,7,4)
            ma25 = MACalc(binanceallcoins2,25,4)
            ma99 = MACalc(binanceallcoins2,99,4)
            wma50 = WMACalc(binanceallcoins2,50,4)
            RSI = calcRSI(binanceallcoins2,4)
            price = float(x['price'])
            ma_tablerow.append(symbol)
            ma_tablerow.append("{:.8f}".format(price))
            ma_tablerow.append("{:.8f}".format(ma7))
            ma_tablerow.append(pricecompare(price,ma7,True))
            ma_tablerow.append("{:.8f}".format(ma25))
            ma_tablerow.append(pricecompare(price,ma25,True))
            ma_tablerow.append("{:.8f}".format(ma99))
            ma_tablerow.append(pricecompare(price,ma99,True))
            ma_tablerow.append(pricecompare(ma25,ma99,True))
            ma_tablerow.append(True)
            ma_tablerow.append("{:.8f}".format(wma50))
            ma_tablerow.append(pricecompare(price,wma50,False))
            ma_tablerow.append("{:.2f}".format(RSI))
            """
            if price < wma25:
                ma_tablerow.append("Küçük")
            else:
                ma_tablerow.append("Büyük")
            """
            ma_table.append(ma_tablerow)
            #currentprogress += currentprogress

            #showprogress(int(currentprogress/totalprogress))

    context = {
        "binanceallcoins":ma_table,
        "interval":interval,
    }
    return render(request, "madurum.html", context)

voltablelast = []
buyvoltablelast = []

def filtervoltable(voltable, count):
    if voltable == []:
        return
    if count == 0:
        for x in voltable:
            x[6] = True
        return voltable
    symbol = voltable[0][0]
    itemcount = 0
    indexstart = 0
    for index, x in enumerate(voltable):
        #if index < 100:
            #print("Başlangıç---",symbol,":",voltable[index][0],":",x[0],":",index)
        if (x[0] == symbol) and index < len(voltable)-1:
            itemcount += 1
            x[6] = False
            #print("Aynı Coin",symbol, "index:", index,"itemcount:",itemcount)
        else:
            if itemcount >= count:
                for i in range(0,itemcount):
                #print("Sıralama ********:",voltable[indexstart+i][0],"index:",index,":", i,"itemcount:",itemcount,":",indexstart,":", infilterzone)
                    voltable[indexstart+i][6] = True
                """
                infilterzone = True
                #print("Yeni Coin +++:",symbol, ":", x[0], itemcount,":",count,":",infilterzone)
            else:
                infilterzone = False
                #print("Yeni Coin ---:",symbol, ":", x[0], itemcount,":",count,":",infilterzone)
                """
            symbol = x[0]
            itemcount = 1
            indexstart = index
            x[6] = False

    """
    for z in voltable:
        print(z)
    """
    return voltable

def trackvolume(request):
    global voltablelast
    Checkboxischecked1 = request.GET.get("checkboxstate1")
    Checkboxischecked2 = request.GET.get("checkboxstate2")
    data_count = request.GET.get("data_count")
    if data_count:
        data_count = int(data_count)
    else:
        data_count = 5
    interval = request.GET.get("timeinterval")
    voltable = []
    if voltablelast and not(Checkboxischecked1):
        voltable = voltablelast
        if Checkboxischecked2:
            filtervoltable(voltable,data_count)
        else:
            filtervoltable(voltable,0)
    elif interval:
        url = "https://api.binance.com/api/v3/ticker/price"
        #http = urllib3.PoolManager()
        #urllib3.disable_warnings()
        #response = http.request('GET', url)
        response = requests.get(url)
        binanceallcoinsx = response.json()
        binanceallcoinsx = filtercoins(binanceallcoinsx)

        limit = "1000"

        for x in binanceallcoinsx:
            symbol = x['symbol']
            start_time = datetime.now() - timedelta(days=5)
            end_time = datetime.now()
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&startTime={}&endTime={}&limit={}".format(symbol, interval, int(datetime.timestamp(start_time)*1000), int(datetime.timestamp(end_time)*1000), limit)
            response = requests.get(url)
            binanceallcoins2 = response.json()
            binanceallcoins2 = maketableforweb(binanceallcoins2)

            #binanceallcoins2.sort(key=lambda x:x[0], reverse = True)

            if len(binanceallcoins2) == 0:
                continue

            for index in range(len(binanceallcoins2)):

                vol1 = float(binanceallcoins2[index][5])
                if index+1 < len(binanceallcoins2):
                    vol2 = float(binanceallcoins2[index+1][5])
                else:
                    vol2 = vol1
                istotalvoladded = False

                volxtable = []

                if vol1 != 0:
                    if ((vol1-vol2)/vol1 >= 0.9) and vol1 >= 2:
                        volxtable.append(symbol)
                        volxtable.append(binanceallcoins2[index][0])
                        volxtable.append(binanceallcoins2[index][5])
                        volxtable.append(binanceallcoins2[index][6])
                        volxtable.append(binanceallcoins2[index][8])
                        volxtable.append(binanceallcoins2[index][3])
                        volxtable.append(True)
                        voltable.append(volxtable)
                        istotalvoladded = True

                volxtable = []

                vol1 = float(binanceallcoins2[index][6])
                if index+1 < len(binanceallcoins2):
                    vol2 = float(binanceallcoins2[index+1][6])
                else:
                    vol2 = vol1

                if vol1 != 0:
                    if ((vol1-vol2)/vol1 >= 0.9) and vol1 >= 2:
                        if not(istotalvoladded):
                            volxtable.append(symbol)
                            volxtable.append(binanceallcoins2[index][0])
                            volxtable.append(binanceallcoins2[index][5])
                            volxtable.append(binanceallcoins2[index][6])
                            volxtable.append(binanceallcoins2[index][8])
                            volxtable.append(binanceallcoins2[index][3])
                            volxtable.append(True)
                            voltable.append(volxtable)
        voltable.sort()
        voltablelast = voltable

    context = {
        "voltable":voltable,
        "interval":interval,
        "limit":data_count
    }
    return render(request, "hacimtakip.html", context)

def trackbuyvolume(request):
    global buyvoltablelast
    Checkboxischecked1 = request.GET.get("checkboxstate1")
    Checkboxischecked2 = request.GET.get("checkboxstate2")
    data_count = request.GET.get("data_count")
    if data_count:
        data_count = int(data_count)
    else:
        data_count = 5
    interval = request.GET.get("timeinterval")
    voltable = []
    if buyvoltablelast and not(Checkboxischecked1):
        voltable = buyvoltablelast
        if Checkboxischecked2:
            filtervoltable(voltable,data_count)
        else:
            filtervoltable(voltable,0)
    elif interval:
        url = "https://api.binance.com/api/v3/ticker/price"
        #http = urllib3.PoolManager()
        #urllib3.disable_warnings()
        #response = http.request('GET', url)
        response = requests.get(url)
        binanceallcoinsx = response.json()
        binanceallcoinsx = filtercoins(binanceallcoinsx)

        limit = "1000"

        for x in binanceallcoinsx:
            symbol = x['symbol']
            start_time = datetime.now() - timedelta(days=5)
            end_time = datetime.now()
            url = "https://api.binance.com/api/v1/klines?symbol={}&interval={}&startTime={}&endTime={}&limit={}".format(symbol, interval, int(datetime.timestamp(start_time)*1000), int(datetime.timestamp(end_time)*1000), limit)
            response = requests.get(url)
            binanceallcoins2 = response.json()
            binanceallcoins2 = maketableforweb(binanceallcoins2)

            #binanceallcoins2.sort(key=lambda x:x[0], reverse = True)

            if len(binanceallcoins2) == 0:
                continue

            for index in range(len(binanceallcoins2)):

                vol1 = float(binanceallcoins2[index][6])
                if index+1 < len(binanceallcoins2):
                    vol2 = float(binanceallcoins2[index+1][6])
                else:
                    vol2 = vol1

                volxtable = []

                if vol1 != 0:
                    if ((vol1-vol2)/vol1 >= 0.9) and vol1 >= 2:
                        volxtable.append(symbol)
                        volxtable.append(binanceallcoins2[index][0])
                        volxtable.append(binanceallcoins2[index][5])
                        volxtable.append(binanceallcoins2[index][6])
                        volxtable.append(binanceallcoins2[index][8])
                        volxtable.append(binanceallcoins2[index][3])
                        volxtable.append(True)
                        voltable.append(volxtable)

        voltable.sort()
        buyvoltablelast = voltable

    context = {
        "voltable":voltable,
        "interval":interval,
        "limit":data_count
    }
    return render(request, "hacimtakip.html", context)

def find_tweets(request):
    from selenium import webdriver
    import time

    context = dict()

    if request.GET.get("tweet_querry"):

        browser = webdriver.Firefox()
        browser.get("https://twitter.com/search-home")

        searchArea = browser.find_element_by_xpath("//*[@id='search-home-input']")
        try:
            searchButton = browser.find_element_by_xpath("/html/body/div[2]/div[2]/div/div[2]/div[1]/form/div[2]/button")
        except Exception:
            return render(request, "tweets.html", context)

        searchArea.send_keys(request.GET.get("tweet_querry"))
        searchButton.click()
        time.sleep(2)

        sortbylast = browser.find_element_by_xpath("/html/body/div[2]/div[2]/div/div[1]/div[2]/div/ul/li[2]/a")
        sortbylast.click()
        time.sleep(2)

        lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        counter = 0
        time.sleep(5)
        while(match==False):
            lastCount = lenOfPage
            time.sleep(5)
            lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            if (lastCount == lenOfPage) or (counter == 10):
                match=True
            counter += 1
        time.sleep(3)

        tweets = []

        elements = browser.find_elements_by_css_selector(".TweetTextSize.js-tweet-text.tweet-text")

        for index, element in enumerate(elements):
            #blacklist = ["Join", "join", "sign", "Sign", "Price", "price", "Binance"]
            isinblacklist = False
            if element.text.count("$") > 4:
                isinblacklist = True
            """
            else:
                for y in blacklist:
                    if element.text.find(y) != -1:
                        isinblacklist = True
                        break
            """
            if not isinblacklist:
                tweets.append(str(index)+". " + element.text)

        #browser.close()

        context = {
            "searched_result" : tweets,
            "tweet_querry" : request.GET.get("tweet_querry"),
        }

    return render(request, "tweets.html", context)

def plotcoin(request):
    import json
    import pandas as pd
    import matplotlib.pyplot as pyplot
    from stockstats import StockDataFrame
    from matplotlib import pylab
    #from pylab import *
    from io import StringIO
    import PIL, PIL.Image

    url = 'https://www.binance.com/api/v1/klines?symbol=BTCUSDT&interval=1d'
#Binance api adresi symbol= den sonra istediğiniz sembol ü yazabilirsiniz.
#interval= dan sonrada istediğiniz zaman dilimi 1d,4h,15m gibi


    names=['Opentime','Open','High','Low','Close','Volume','Closetime','Quoteassetvolume','Numberoftrades',
       'Takerbuybaseassetvolume','Takerbuyquoteassetvolume','Ignore']
#Gelen kolonların isimleri binance yeni kolon eklemediği sürece değiştirilmesine gerek yok.

    #response = urllib.urlopen(url) #Binance api linkine istek atıyoruz.
    #response = requests.get(url)

    #print("ok response")
    #df = pandas.read_json(response.json(),orient="records") #dönen response u okuyup pandas datayapısına alıyoruz.
    data = json.loads(requests.get(url).text)
    df = pd.DataFrame(data)
    df.to_csv('BinanceTest.csv', encoding='utf-8', index=False, header=False)#CSV dosyası olarak kaydediyoruz.

    dataframe = pd.read_csv('BinanceTest.csv', names=names) #CSV deki dataları kolon isimleri ile alıyoruz.


    stock = StockDataFrame.retype(dataframe) #stockstats kütüphanesinin hesaplamaları için gerekli veri tipine dönüştürüyoruz.
    calc=stock.get('close_50_sma') #kapanış fiyatına göre SMA 50 hesaplanıyor
    calc2=stock.get('close_20_sma') #kapanış fiyatına göre SMA 20 hesaplanıyor

    dataframe.opentime=pd.to_datetime(dataframe.opentime,unit='ms') #Binance linux timestamp gönderiyor zamanı bunu düzgün zaman yapısına çeviriyoruz.

    pyplot.subplot(211)
    pyplot.title('BTC-USD')
    pyplot.plot(dataframe.opentime,dataframe.close)
#İstediğimiz paritenin kapanış fiyatına göre çizdiriyoruz.

    pyplot.subplot(212)
    pyplot.title('SMA(50)-SMA(20)')
    pyplot.plot(dataframe.opentime, calc,dataframe.opentime,calc2)
    #pyplot.show()

    buffer = StringIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")

    pylab.close()

    # Send buffer in a http response the the browser with the mime type image/png set
    return HttpResponse(buffer.getvalue(), mimetype="image/png")



def get_session_supply(session_supply):
    for item in session_supply:
        temp = item.text[:item.text.find(" ")]
        error = False
        try:
            temp = temp.replace(",","")
            int(temp)
            #print(temp)
        except:
            error = True
            #print("Error----------\n",temp)
        if not(error):
            return temp
    return None

def Binance_ICO_Page(url):
    http = urllib3.PoolManager()
    urllib3.disable_warnings()
    response = http.request('GET', url)
    #print(url)
    if response.status != 200:
        print("HATA: Source Page did not load....")
    html_icerigi = response.data
    soup =  BeautifulSoup(html_icerigi,"html.parser")
    tds = soup.find_all("td")
    ICO_data = []
    for item in tds:
        if item.text[len(item.text)-1] == " ":
            ICO_data.append(item.text[:len(item.text)-1])
        else:
            ICO_data.append(item.text)
    return dict(zip(ICO_data[::2], ICO_data[1::2]))

def Binance_LP():

    #default_headers = urllib3.make_headers(proxy_basic_auth='myusername:mypassword')
    http = urllib3.ProxyManager("http://proxy.server:3128")#, headers=default_headers)
    #proxy = urllib3.ProxyManager('http://localhost:3128/')
    #>>> proxy.request('GET', 'http://google.com/')

    # Now you can use `http` as you would a normal PoolManager
    #r = http.request('GET', 'https://stackoverflow.com/')

    url =  "http://launchpad.binance.com" # Site linkimiz
    #http = urllib3.PoolManager()
    urllib3.disable_warnings()
    #f = urllib.request.urlopen(url)
    #html_icerigi = f.read().decode('utf-8')
    #return None
    response = http.request('GET', url)
    if response.status != 200:
        print("HATA: Source Page did not load....")
    #print(response.data)

    html_icerigi = response.data  # Web sayfamızın içeriğini alıyoruz.
    return html_icerigi
    soup =  BeautifulSoup(html_icerigi,"html.parser") # Web sayfamızı parçalamak için BeautifulSoup objesine atıyoruz.
    script = soup.find("script").text
    script_ico_data = []
    all_ICO_data = []
    reference_time = datetime.now() - timedelta(days=45)

    if "__NEXT_DATA__ =" in script:
    #print("BULDUMMMMMM")
        x = script.find("[")
        y = script.find("]")
        script = script[x+1:y]
    #print(script,"\n",x,":",y)
        itemindex = 1

        while script.find("}") != -1:
            item = script[:script.find("}")+1]
            #print(itemindex,"------------\n",item)
            script = script[script.find("}")+2:]
            itemindex += 1
            todict = json.loads(item)
            script_ico_data.append(todict)
            #todict = json.dumps(script,indent=4)
            #print(todict,"\n",type(todict))
    #print(soup)
    #print(soup.prettify()) # Daha güzel bir görüntü için prettify() fonksiyonunu kullanıyoruz.
    #print("SOUP2", soup2)
    soup2 = BeautifulSoup(str(soup.find("ul", attrs={"class": "hpqqd2-3 jSMYRG"})),"html.parser")
    #print(soup2)
    index = 1
    for element in soup2.find_all("li"):
        soup3 = BeautifulSoup(str(element),"html.parser")
        ico_link = soup3.find("a")
        session_supply = soup3.find("div",  attrs={"class": "hpqqd2-3 jSMYRG"})
        session_supply = BeautifulSoup(str(session_supply),"html.parser")
        session_supply = soup3.find_all("span")
        session_supply =  get_session_supply(session_supply)
        ICO_Page_Data = dict()
        ICO_Page_Data["Session_Supply"] = session_supply
        if ico_link != None:
            ico_link = ico_link.get("href")
            ICO_Page_Data["Link"] = url+ico_link
        else:
            ICO_Page_Data["Link"] = None
        ico_name = soup3.find("h2").text
        ICO_Page_Data["Name"] = ico_name
        #print(i.get("href"))
        end_time = int(script_ico_data[index-1]['time'])
        end_time = datetime.fromtimestamp(end_time / 1000)
        if end_time > reference_time:

            ICO_Page_Data["End_Time"] = end_time
            #print(index, "\n-----------------\n", ico_link,"\n",ico_name,"\n",session_supply,"\n",end_time)

            if ico_link != None:
                ICO_Page = Binance_ICO_Page(url+ico_link)
                #print(ICO_Page,"\n",url+ico_link)

                if ICO_Page != []:
                    keys = ["Total Token Supply","Initial Circulating Supply","Public Sale Token Price","Token Sale Start Time"]
                    for key in keys:
                        try:
                            ICO_Page_Data[key.replace(" ","_")] = ICO_Page[key]

                        except:
                            ICO_Page_Data[key.replace(" ","_")] = "N/A"


                #print(ICO_Page_Data)
            if ICO_Page_Data["Token_Sale_Start_Time"] == "N/A":
                ICO_Page_Data["Token_Sale_Start_Time"] = ICO_Page_Data["End_Time"]
            else:
                ICO_Page_Data["Token_Sale_Start_Time"] =  ICO_Page_Data["Token_Sale_Start_Time"].replace(" (UTC)","")
                try:
                    ICO_Page_Data["Token_Sale_Start_Time"] =  datetime.strptime(ICO_Page_Data["Token_Sale_Start_Time"], '%Y/%m/%d %H:%M %p')
                except:
                    error = True
            all_ICO_data.append(ICO_Page_Data)
        index += 1
    return all_ICO_data


def ICOs(request):
    all_ICO_data = Binance_LP()

    context = {
        "all_ICO_data":all_ICO_data,
    }
    return render(request, "ICOs.html", context)