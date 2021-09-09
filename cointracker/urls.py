"""cointracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from binancecoins import views

app_name = "binanceallcoins"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name = "index"),
    path('arsiv/', views.arsiv, name = "arsiv"),
    path('about/', views.about, name = "about"),
    path('test/', views.test, name = "test"),
    path('coinlist/', views.coinlist, name = "coinlist"),
    path('deleteallcoin/', views.deleteallcoin, name = "deleteallcoin"),
    path('update/<str:id>', views.update,name="update"),
    path('minmax/', views.minmax, name = "minmax"),
    path('madurum/', views.madurum, name = "madurum"),
    path('trackvolume/', views.trackvolume, name = "volumes"),
    path('trackbuyvolume/', views.trackbuyvolume, name = "buyvolumes"),
    path('ICOs/', views.ICOs, name = "ICOs"),
]
