from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search', views.search, name='search'),
    path('new-listing', views.newListing, name='newListing'),
    path('my-listings', views.myListings, name='myListings'),
    path('my-account', views.myAccount, name='myAccount'),
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('delete-confirm', views.deleteConfirm, name='deleteConfirm'),
    path('listing-<int:number>', views.listingPurchase, name='listingPurchase'),
    path('edit-listing-<int:number>', views.listingEdit, name='listingEdit'),
    path('del-listing-<int:number>', views.listingDelete, name='listingDelete'),
]
