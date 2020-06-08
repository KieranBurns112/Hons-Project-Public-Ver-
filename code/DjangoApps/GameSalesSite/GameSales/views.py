from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from GameSales.models import Listings, Users
from decimal import Decimal
import os

platforms = ["Playstation 4", "Xbox One", "Nintendo Switch", "PC"]
sortTypes = ["Newest First", "Oldest First", "Price (Low-High)", "Price (High-Low)"]

def loginStatus(request):
    try:
        return request.session['logged']
    except:
        return False

def getUsername(request):
    try:
        return request.session['username']
    except:
        return ""

def handler404(request, *args, **argv):
    response = render('404.html', {})
    response.status_code = 404
    return response

def home(request):
    listings = []
    results = 0

    allRows = Listings.objects.using('listings_db').all()

    for row in allRows:
        temp = []
        temp.append(row.game)
        temp.append(row.platform)
        temp.append(row.price)
        temp.append(row.seller)
        temp.append(row.id)
        listings.append(temp)
        results+=1

    return render(request, 'mainPage.html', {
        'pageType' : "home",
        'listings' : listings,
        'results' : results,
        'order' : "descending",
        'signedIn' : loginStatus(request),
        'username' : getUsername(request),
    })

def search(request):
    if request.method == "POST":
        listings = []
        results = 0
        order = ""

        title = request.POST["title"]
        platform = request.POST["platform"]
        sortBy = request.POST["sortCriteria"]

        allRows = Listings.objects.using('listings_db').all()
        allRows = allRows.filter(game__icontains=title)
        if not platform == "All":
            allRows = allRows.filter(platform=platform)

        for row in allRows:
            temp = []
            temp.append(row.game)
            temp.append(row.platform)
            temp.append(row.price)
            temp.append(row.seller)
            temp.append(row.id)
            listings.append(temp)
            results+=1

        if sortBy == "Newest First":
            order = "descending"
        elif sortBy == "Oldest First":
            order = "ascending"
        elif sortBy == "Price (Low-High)" or sortBy == "Price (High-Low)":
            if sortBy == "Price (Low-High)":
                order = "ascending"
            else:
                order = "descending"

            for i in range(results):
                listings[i][2] = Decimal(listings[i][2])
            listings.sort(key=lambda x:x[2])

        return render(request, 'mainPage.html', {
            'pageType' : "search-results",
            'listings' : listings,
            'results' : results,
            'order' : order,
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        })
    else:
        return render(request, 'search.html', {
            'platforms' : platforms,
            'sortTypes' : sortTypes,
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        })

def newListing(request):
    if request.method == "POST":
        valid = True
        error = "none"

        newTitle = request.POST["title"]
        newPlatform = request.POST["platform"]
        newPrice = request.POST["price"]

        if newTitle == "":
            valid = False
            error = "No title entered!"
        else:
            platformselected = False
            for platform in platforms:
                if newPlatform == platform:
                    platformselected = True

            if not platformselected:
                valid = False
                error = "Invalid Platform! Use the dropdown menu to select the platform."
            else:
                try:
                    decimalPrice = Decimal(newPrice)
                    decimalPrice += 1
                    if not len(newPrice.rsplit('.')[-1]) == 2:
                        valid = False
                        error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"
                except:
                    valid = False
                    error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"
        if valid:
            newDBListing = Listings(
                game = newTitle,
                platform = newPlatform,
                price = newPrice,
                seller = getUsername(request)
            )

            newDBListing.save(using='listings_db')

            return redirect('/')
        else:
            return render(request, 'newListing.html', {
                'pageTitle' : "New Listing",
                'platforms' : platforms,
                'error' : error,
                'currentTitle' :"",
                'currentPlatform' : "",
                'currentPrice' : "",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
    else:
        if loginStatus(request):
            return render(request, 'newListing.html', {
                'pageTitle' : "New Listing",
                'platforms' : platforms,
                'error' : "none",
                'currentTitle' :"",
                'currentPlatform' : "",
                'currentPrice' : "",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
        else:
            return redirect('/login')

def myListings(request):
    if loginStatus(request):
        listings = []
        results = 0

        allRows = Listings.objects.using('listings_db').all()
        allRows = allRows.filter(seller=getUsername(request))

        for row in allRows:
            temp = []
            temp.append(row.game)
            temp.append(row.platform)
            temp.append(row.price)
            temp.append(row.seller)
            temp.append(row.id)
            listings.append(temp)
            results+=1


        return render(request, 'mainPage.html', {
            'pageType' : "my-listings",
            'listings' : listings,
            'results' : results,
            'order' : "descending",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        })
    else:
        return redirect('/login')

def myAccount(request):
    if request.method == "POST":
        valid = True
        error = "none"

        oldPassword = request.POST["oldPassword"]
        newPassword = request.POST["newPassword"]
        reNewPassword = request.POST["reNewPassword"]

        dbResult = Users.objects.using('users_db').get(username=getUsername(request))
        hash = User(password = dbResult.password)
        if not hash.check_password(oldPassword):
            valid = False
            error = "Old Password is Incorrect!"
        else:
            if newPassword != reNewPassword:
                valid = False
                error = "Passwords do not match!"

        if valid:
            hash.set_password(newPassword)
            dbResult.password = hash.password
            # Location does not need specified since it's already
            # part of dbResult.
            dbResult.save()

            return redirect('/')
        else:
            return render(request, 'myAccount.html', {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })

    else:
        if loginStatus(request):
            return render(request, 'myAccount.html', {
                'error' : "none",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
        else:
            return redirect('/login')

def signup(request):
    if request.method == "POST":
        valid = True
        error = "none"

        username = request.POST["username"]
        password = request.POST["password"]
        rePassword = request.POST["rePassword"]

        # Query the DB to see if username exists, if it doesn't,
        # an exception is thrown.
        try:
            Users.objects.using('users_db').get(username=username)
            result = True
        except:
            result = False

        if result or username == "":
            valid = False
            error = "Username aready exists! Did you mean to log in?"
        else:
            if password != rePassword:
                valid = False
                error = "Passwords do not match!"

        if valid:
            # Create a new User() with only a password which will
            # be hashed automatically by Django-bcrypt.
            hash = User()
            hash.set_password(password)

            newDBUser = Users(
                username = username,
                password = hash.password
            )

            #Write the users model to the db.
            newDBUser.save(using='users_db')

            return redirect("/login")
        else:
            return render(request, 'signup.html', {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
    else:
        return render(request, 'signup.html', {
            'error' : "none",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        })

def login(request):
    if request.method == "POST":
        valid = True

        username = request.POST["username"]
        password = request.POST["password"]

        if username != "":
            try:
                dbResult = Users.objects.using('users_db').get(username=username)
                hash = User(password = dbResult.password)
                if not hash.check_password(password):
                    valid = False
            except:
                valid = False
        else:
            valid = False

        if valid:
            request.session['logged'] = True
            request.session['username'] = username
            return redirect('/')
        else:
            error = "Username or Password Incorrect!"
            return render(request, 'login.html', {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
    else:
        return render(request, 'login.html', {
            'error' : "none",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        })

def logout(request):
    request.session['logged'] = False
    request.session['username'] = ""
    return redirect("/")

def deleteConfirm(request):
    if request.method == "POST":
        Listings.objects.using('listings_db').filter(seller=getUsername(request)).delete()
        Users.objects.using('users_db').get(username=getUsername(request)).delete()
        return redirect("/logout")
    else:
        if loginStatus(request):
            return render(request, 'deleteConfirm.html', {
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
        else:
            return redirect('/login')

def listingPurchase(request, number):
    #"number" taken for unimplemented features.

    # No simple way of loading a static HTML page from the static folder,
    # loading the file from templates without any parameters suffices.
    return render(request, 'notImplemented.html')

def listingEdit(request, number):
    thisListing = Listings.objects.using('listings_db').get(id=number)
    if request.method == "POST":
        valid = True
        error = "none"

        newTitle = request.POST["title"]
        newPlatform = request.POST["platform"]
        newPrice = request.POST["price"]

        if newTitle == "":
            valid = False
            error = "No title entered!"
        else:
            platformselected = False
            for platform in platforms:
                if newPlatform == platform:
                    platformselected = True

            if not platformselected:
                valid = False
                error = "Invalid Platform! Use the dropdown menu to select the platform."
            else:
                try:
                    decimalPrice = Decimal(newPrice)
                    decimalPrice += 1
                    if not len(newPrice.rsplit('.')[-1]) == 2:
                        valid = False
                        error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"
                except:
                    valid = False
                    error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"

        if valid:
            thisListing.game = newTitle
            thisListing.platform = newPlatform
            thisListing.price = newPrice
            thisListing.seller = getUsername(request)
            thisListing.save()

            return redirect('/')
        else:
            return render(request, 'newListing.html', {
                'pageTitle' : "Edit Listing",
                'platforms' : platforms,
                'error' : error,
                'currentTitle' : thisListing.game,
                'currentPlatform' : thisListing.platform,
                'currentPrice' : thisListing.price,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            })
    else:
        if loginStatus(request):
            try:
                if thisListing.seller == getUsername(request):
                    return render(request, 'newListing.html', {
                        'pageTitle' : "Edit Listing",
                        'platforms' : platforms,
                        'error' : "none",
                        'currentTitle' : thisListing.game,
                        'currentPlatform' : thisListing.platform,
                        'currentPrice' : thisListing.price,
                        'signedIn' : loginStatus(request),
                        'username' : getUsername(request),
                    })
                else:
                    return redirect('/')
            except:
                return redirect('/')
            else:
                return redirect('/login')

def listingDelete(request, number):
    try:
        thisListing = Listings.objects.using('listings_db').get(id=number)
        if thisListing.seller == getUsername(request):
            thisListing.delete()
        return redirect('/')
    except:
        return redirect('/')
