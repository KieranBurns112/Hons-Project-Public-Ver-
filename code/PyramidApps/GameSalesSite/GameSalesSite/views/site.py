from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from passlib.hash import bcrypt
from .. import models
from decimal import Decimal
from os import path
import sqlalchemy as db

platforms = ["Playstation 4", "Xbox One", "Nintendo Switch", "PC"]
sortTypes = ["Newest First", "Oldest Fsirst", "Price (Low-High)", "Price (High-Low)"]

folder_path = path.dirname(__file__)

listings_path = path.abspath(path.join(
    folder_path,
    "..",
    "databases",
    "listings.db"
))

users_path = path.abspath(path.join(
    folder_path,
    "..",
    "databases",
    "users.db"
))

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

@view_config(context=HTTPNotFound, renderer='../templates/404.jinja2')
def error404(request):
    request.response.status = 404
    return {'wrongURL' : request.url}

@view_config(route_name='home', renderer='../templates/mainPage.jinja2')
def home(request):
    listings = []
    results = 0

    engine = db.create_engine('sqlite:///' + listings_path)
    connection = engine.connect()
    metadata = db.MetaData()
    listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

    query = db.select([listings_db])
    allRows = connection.execute(query).fetchall()

    for row in allRows:
        temp = []
        temp.append(row.game)
        temp.append(row.platform)
        temp.append(row.price)
        temp.append(row.seller)
        temp.append(row.id)
        listings.append(temp)
        results+=1

    return {
        'pageType' : "home",
        'listings' : listings,
        'results' : results,
        'order' : "descending",
        'signedIn' : loginStatus(request),
        'username' : getUsername(request),
    }

@view_config(route_name='search', renderer='../templates/search.jinja2')
def search(request):
    if request.method == "POST":
        listings = []
        results = 0
        order = ""

        title = request.POST["title"]
        platform = request.POST["platform"]
        sortBy = request.POST["sortCriteria"]

        engine = db.create_engine('sqlite:///' + listings_path)
        connection = engine.connect()
        metadata = db.MetaData()
        listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

        if platform == "All":
            query = db.select([listings_db]).where(
                listings_db.c.game.contains(title)
            )
        else:
            query = db.select([listings_db]).where(db.and_(
                listings_db.c.game.contains(title),
                listings_db.c.platform == platform
            ))

        allRows = connection.execute(query).fetchall()

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

        return render_to_response('../templates/mainPage.jinja2', {
            'pageType' : "search-results",
            'listings' : listings,
            'results' : results,
            'order' : order,
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        }, request=request)
    else:
        return {
            'platforms' : platforms,
            'sortTypes' : sortTypes,
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        }

@view_config(route_name='newListing', renderer='../templates/newListing.jinja2')
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
            engine = db.create_engine('sqlite:///' + listings_path)
            connection = engine.connect()
            metadata = db.MetaData()
            listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

            query = db.insert(listings_db).values(
                game = newTitle,
                platform = newPlatform,
                price = newPrice,
                seller = getUsername(request)
            )
            connection.execute(query)

            url = request.route_url('home')
            return HTTPFound(location=url)
        else:
            return {
                'pageTitle' : "New Listing",
                'platforms' : platforms,
                'error' : error,
                'currentTitle' :"",
                'currentPlatform' : "",
                'currentPrice' : "",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
    else:
        if loginStatus(request):
            return {
                'pageTitle' : "New Listing",
                'platforms' : platforms,
                'error' : "none",
                'currentTitle' :"",
                'currentPlatform' : "",
                'currentPrice' : "",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
        else:
            url = request.route_url('login')
            return HTTPFound(location=url)

@view_config(route_name='myListings', renderer='../templates/mainPage.jinja2')
def myListings(request):
    if loginStatus(request):
        listings = []
        results = 0

        engine = db.create_engine('sqlite:///' + listings_path)
        connection = engine.connect()
        metadata = db.MetaData()
        listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

        query = db.select([listings_db]).where(
            listings_db.c.seller == getUsername(request)
        )

        allRows = connection.execute(query).fetchall()

        for row in allRows:
            temp = []
            temp.append(row.game)
            temp.append(row.platform)
            temp.append(row.price)
            temp.append(row.seller)
            temp.append(row.id)
            listings.append(temp)
            results+=1

        return {
            'pageType' : "my-listings",
            'listings' : listings,
            'results' : results,
            'order' : "descending",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        }
    else:
        url = request.route_url('login')
        return HTTPFound(location=url)

@view_config(route_name='myAccount', renderer='../templates/myAccount.jinja2')
def myAccount(request):
    if request.method == "POST":
        valid = True
        error = "none"

        oldPassword = request.POST["oldPassword"]
        newPassword = request.POST["newPassword"]
        reNewPassword = request.POST["reNewPassword"]

        engine = db.create_engine('sqlite:///' + users_path)
        connection = engine.connect()
        metadata = db.MetaData()
        users_db = db.Table('users', metadata, autoload=True, autoload_with=engine)

        query = db.select([users_db]).where(
            users_db.c.username == getUsername(request)
        )
        thisUser = connection.execute(query).fetchone()

        if not bcrypt.verify(oldPassword, thisUser.password):
            valid = False
            error = "Old Password is Incorrect!"
        else:
            if newPassword != reNewPassword:
                valid = False
                error = "Passwords do not match!"

        if valid:
            encryptedNewPw = bcrypt.hash(newPassword)
            query = db.update(users_db).values(
                password = encryptedNewPw
            ).where(
                users_db.c.username == getUsername(request)
            )
            connection.execute(query)

            url = request.route_url('home')
            return HTTPFound(location=url)
        else:
            return {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
    else:
        if loginStatus(request):
            return {
                'error' : "none",
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
        else:
            url = request.route_url('login')
            return HTTPFound(location=url)

@view_config(route_name='signup', renderer='../templates/signup.jinja2')
def signup(request):
    if request.method == "POST":
        valid = True
        error = "none"

        username = request.POST["username"]
        password = request.POST["password"]
        rePassword = request.POST["rePassword"]

        engine = db.create_engine('sqlite:///' + users_path)
        connection = engine.connect()
        metadata = db.MetaData()
        users_db = db.Table('users', metadata, autoload=True, autoload_with=engine)

        try:
            query = db.select([users_db]).where(
                users_db.c.username == username
            )
            existingUser = connection.execute(query).fetchone()

            if existingUser.username == username:
                result = True
            else:
                result = False
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
            query = db.insert(users_db).values(
                username = username,
                password = bcrypt.hash(password)
            )
            connection.execute(query)

            url = request.route_url('login')
            return HTTPFound(location=url)
        else:
            return {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
    else:
        return {
            'error' : "none",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        }

@view_config(route_name='login', renderer='../templates/login.jinja2')
def login(request):
    if request.method == "POST":
        valid = True

        username = request.POST["username"]
        password = request.POST["password"]

        engine = db.create_engine('sqlite:///' + users_path)
        connection = engine.connect()
        metadata = db.MetaData()
        users_db = db.Table('users', metadata, autoload=True, autoload_with=engine)

        if username != "":
            try:
                query = db.select([users_db]).where(
                    users_db.c.username == username
                )
                dbResult = connection.execute(query).fetchone()

                if not bcrypt.verify(password, dbResult.password):
                    valid = False
            except:
                valid = False
        else:
            valid = False

        if valid:
            request.session['logged'] = True
            request.session['username'] = username
            url = request.route_url('home')
            return HTTPFound(location=url)
        else:
            error = "Username or Password Incorrect!"
            return {
                'error' : error,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
    else:
        return {
            'error' : "none",
            'signedIn' : loginStatus(request),
            'username' : getUsername(request),
        }

@view_config(route_name='logout')
def logout(request):
    request.session['logged'] = False
    request.session['username'] = ""
    url = request.route_url('home')
    return HTTPFound(location=url)

@view_config(route_name='deleteConfirm', renderer='../templates/deleteConfirm.jinja2')
def deleteConfirm(request):
    if request.method == "POST":
        engine = db.create_engine('sqlite:///' + listings_path)
        connection = engine.connect()
        metadata = db.MetaData()
        listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

        query = listings_db.delete().where(
            listings_db.c.seller == getUsername(request)
        )
        connection.execute(query)

        engine = db.create_engine('sqlite:///' + users_path)
        connection = engine.connect()
        metadata = db.MetaData()
        users_db = db.Table('users', metadata, autoload=True, autoload_with=engine)

        query = users_db.delete().where(
            users_db.c.username == getUsername(request)
        )
        connection.execute(query)

        url = request.route_url('logout')
        return HTTPFound(location=url)
    else:
        if loginStatus(request):
            return {
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
        else:
            url = request.route_url('login')
            return HTTPFound(location=url)

@view_config(route_name='listingPurchase')
def listingPurchase(request):
    # Since, much like Django, there is no "easy way" of rendering static
    # html, this was the simplist alternative to the problem. Alternatively,
    # it is possible for a developer to write and implement their own renderer,
    # however this would be excessive in the scope of this project.
    return render_to_response('../static/html/notImplemented.html.jinja2',
        {}, request=request)

@view_config(route_name='listingEdit', renderer='../templates/newListing.jinja2')
def listingEdit(request):
    engine = db.create_engine('sqlite:///' + listings_path)
    connection = engine.connect()
    metadata = db.MetaData()
    listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

    query = db.select([listings_db]).where(
        listings_db.c.id == request.matchdict['number']
    )
    thisListing = connection.execute(query).fetchone()

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
            query = db.update(listings_db).values(
                game = newTitle,
                platform = newPlatform,
                price = newPrice
            ).where(
                listings_db.c.id == request.matchdict['number']
            )
            connection.execute(query)

            url = request.route_url('home')
            return HTTPFound(location=url)
        else:
            return {
                'pageTitle' : "Edit Listing",
                'platforms' : platforms,
                'error' : error,
                'currentTitle' : thisListing.game,
                'currentPlatform' : thisListing.platform,
                'currentPrice' : thisListing.price,
                'signedIn' : loginStatus(request),
                'username' : getUsername(request),
            }
    else:
        if loginStatus(request):
            try:
                if thisListing.seller == getUsername(request):
                    return {
                        'pageTitle' : "Edit Listing",
                        'platforms' : platforms,
                        'error' : "none",
                        'currentTitle' : thisListing.game,
                        'currentPlatform' : thisListing.platform,
                        'currentPrice' : thisListing.price,
                        'signedIn' : loginStatus(request),
                        'username' : getUsername(request),
                    }
                else:
                    url = request.route_url('home')
                    return HTTPFound(location=url)
            except:
                url = request.route_url('home')
                return HTTPFound(location=url)
            else:
                url = request.route_url('login')
                return HTTPFound(location=url)

@view_config(route_name='listingDelete')
def listingDelete(request):
        engine = db.create_engine('sqlite:///' + listings_path)
        connection = engine.connect()
        metadata = db.MetaData()
        listings_db = db.Table('listings', metadata, autoload=True, autoload_with=engine)

        query = db.select([listings_db]).where(
            listings_db.c.id == request.matchdict['number']
        )
        thisListing = connection.execute(query).fetchone()

        if thisListing.seller == getUsername(request):
            query = listings_db.delete().where(
                listings_db.c.id == request.matchdict['number']
            )
            connection.execute(query)
        url = request.route_url('home')
        return HTTPFound(location=url)
