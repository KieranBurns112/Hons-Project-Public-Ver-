# To Run:
# cd [-LocalDirectoryLocation-]\FlaskApps\GameSalesSite
# flask run

from flask import Flask, render_template, request, redirect, session
from decimal import Decimal
import os
import bcrypt
import sqlite3


app = Flask(__name__)

# Sufficiently Random secret_key setup
app.secret_key=os.urandom(24)

# Databases used. These could be stored in external locations.
listingsDB = "databases/listings.db"
usersDB = "databases/users.db"

# Dropdown Menu Contents
platforms = ["Playstation 4", "Xbox One", "Nintendo Switch", "PC"]
sortTypes = ["Newest First", "Oldest First", "Price (Low-High)", "Price (High-Low)"]

# Methods to get current session information.
# Methods required as session can be null
def loginStatus():
	try:
		return session["logged"]
	except:
		return False

def getUsername():
    try:
        return session["username"]
    except:
        return ""

@app.errorhandler(404)
def error404(e):
	return render_template('404.html', wrongURL = request.url), 404

@app.route("/")
def home():
	listings = []
	results = 0

	conn = sqlite3.connect(listingsDB)
	cursor = conn.cursor()
	cursor.execute(""" SELECT * FROM listings """)
	rows = cursor.fetchall()
	cursor.close()

	for row in rows:
		temp = []
		temp.append(row[1])
		temp.append(row[2])
		temp.append(row[3])
		temp.append(row[4])
		temp.append(row[0])
		listings.append(temp)
		results+=1

	return render_template("mainPage.html", pageType = "home", results = results,
	listings=listings, order="descending", signedIn = loginStatus(), username = getUsername())

@app.route("/search")
def search():
    return render_template("search.html", signedIn = loginStatus(), platforms=platforms,
    sortTypes=sortTypes ,username = getUsername())

@app.route("/new-listing")
def newListing():
    if loginStatus():
        return render_template("newListing.html", signedIn = loginStatus(), error="none",
        pageTitle="New Listing", platforms=platforms ,username = getUsername())
    else:
        return redirect("/login")

@app.route("/my-listings")
def myListings():
    if loginStatus():
        listings = []
        results = 0

        conn = sqlite3.connect(listingsDB)
        cursor = conn.cursor()
        cursor.execute(" SELECT * FROM listings WHERE seller=(?)", (getUsername(),))
        rows = cursor.fetchall()
        cursor.close()

        for row in rows:
            temp = []
            temp.append(row[1])
            temp.append(row[2])
            temp.append(row[3])
            temp.append(row[4])
            temp.append(row[0])
            listings.append(temp)
            results+=1

        return render_template("mainPage.html", pageType = "my-listings", results = results,
        listings=listings, order="descending", signedIn = loginStatus(), username = getUsername())
    else:
        return redirect("/login")

@app.route("/my-account")
def myAccount():
    if loginStatus():
        return render_template("myAccount.html", signedIn = loginStatus(), error="none", username = getUsername())
    else:
        return redirect("/login")

@app.route("/signup")
def signup():
    return render_template("signup.html", signedIn = loginStatus(), error="none", username = getUsername())

@app.route("/login")
def login():
    return render_template("login.html", signedIn = loginStatus(), error="none", username = getUsername())

@app.route("/logout")
def logout():
    session["username"] = ""
    session["logged"] = False
    return redirect("/")

@app.route("/delete-confirm")
def deleteConfirm():
    if loginStatus():
        return render_template("deleteConfirm.html", signedIn = loginStatus(), username = getUsername())
    else:
        return redirect("/login")

@app.route("/listing-<number>")
def listingPurchase(number):
    return app.send_static_file("html/notImplemented.html")

@app.route("/edit-listing-<number>")
def listingEdit(number):
    if loginStatus():
        try:
            conn = sqlite3.connect(listingsDB)
            cursor = conn.cursor()
            cursor.execute(""" SELECT seller FROM listings WHERE id=(?)""", (number,))
            seller = cursor.fetchone()[0]
            cursor.close()

            if seller == getUsername():
                cursor = conn.cursor()
                cursor.execute(""" SELECT game, platform, price FROM listings WHERE id=(?)""", (number,))
                currentInfo = cursor.fetchone()
                cursor.close()

                return render_template("newListing.html", signedIn = loginStatus(), platforms=platforms, pageTitle="Edit Listing", error = "none",
                username = getUsername(), currentTitle = currentInfo[0], currentPlatform = currentInfo[1], currentPrice= currentInfo[2])
            else:
                return redirect("/")
        except:
            return redirect("/")
    else:
        return redirect("/login")

@app.route("/del-listing-<number>")
def listingDelete(number):
    #Ensure number is valid (exists)
    try:
        conn = sqlite3.connect(listingsDB)
        cursor = conn.cursor()
        cursor.execute(""" SELECT seller FROM listings WHERE id=(?)""", (number,))
        seller = cursor.fetchone()[0]
        cursor.close()

        #Ensure person deleting the listing is the listing"s owner
        if seller == getUsername():
            cursor = conn.cursor()
            cursor.execute(""" DELETE FROM listings WHERE id=(?)""", (number,))
            conn.commit()
            cursor.close()

        return redirect("/")
    except:
        return redirect("/")

@app.route("/search", methods=["POST"])
def search_post():
    listings = []
    results = 0
    order = ""

    title = request.form["title"]
    platform = request.form["platform"]
    sortBy = request.form["sortCriteria"]

    conn = sqlite3.connect(listingsDB)
    cursor = conn.cursor()

    if platform == "All":
        cursor.execute(" SELECT * FROM listings WHERE LOWER(game) LIKE LOWER(?)", ("%" + title + "%",))
    else:
        cursor.execute(" SELECT * FROM listings WHERE LOWER(game) LIKE LOWER(?) AND platform = (?)", ("%" + title + "%", platform,))
    rows = cursor.fetchall()

    for row in rows:
        temp = []
        temp.append(row[1])
        temp.append(row[2])
        temp.append(row[3])
        temp.append(row[4])
        temp.append(row[0])
        listings.append(temp)
        results+=1

    cursor.close()

    # Sorting
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

    return render_template("mainPage.html", pageType = "search-results", results = results,
    listings=listings, order=order, signedIn = loginStatus(), username = getUsername())

@app.route("/new-listing", methods=["POST"])
def newListing_post():
    #Input from form
    newTitle = request.form["title"]
    newPlatform = request.form["platform"]
    newPrice = request.form["price"]

    valid = True
    error = "none"

    if newTitle == "":
        valid = False
        error = "No title entered!"
    else:
        # Check if a valid platform has been selected.
        platformSelected = False
        for platform in platforms:
            if newPlatform == platform:
                platformSelected = True

        if not platformSelected:
            valid = False
            error = "Invalid Platform! Use the dropdown menu to select the platform."
        else:
            # Check if a numerical value has been entered for price
            try:
                decimalPrice = Decimal(newPrice)
                decimalPrice += 1
                if not len(newPrice.rsplit(".")[-1]) == 2:
                    valid = False
                    error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"
            except:
                valid = False
                error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"

    if valid:
        conn = sqlite3.connect(listingsDB)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO listings (game, platform, price, seller) VALUES (?, ?, ?, ?)""",
        (newTitle, newPlatform, newPrice, getUsername()))
        conn.commit()
        cursor.close()

        return redirect("/")
    else:
        return render_template("newListing.html", signedIn = loginStatus(), error=error, platforms=platforms,
        pageTitle="New Listing" ,username = getUsername())

@app.route("/my-account", methods=["POST"])
def myAccount_post():
    oldPassword = request.form["oldPassword"]
    newPassword = request.form["newPassword"]
    reNewPassword = request.form["reNewPassword"]

    valid = True
    error = "none"

    conn = sqlite3.connect(usersDB)
    cursor = conn.cursor()
    cursor.execute(""" SELECT password FROM users WHERE username=(?)""", (getUsername(),))
    dbPassword = cursor.fetchone()[0]
    cursor.close()

    if dbPassword != bcrypt.hashpw(oldPassword.encode("utf8"), dbPassword):
        valid = False
        error = "Old Password is Incorrect!"
    else:
        if newPassword != reNewPassword:
            valid = False
            error = "Passwords do not match!"

    if valid:
        cursor = conn.cursor()
        securePassword = bcrypt.hashpw(newPassword.encode("utf8"), bcrypt.gensalt())
        cursor.execute(""" UPDATE users SET password=(?) WHERE username=(?)""",(securePassword, getUsername(),))
        conn.commit()
        cursor.close()

        return redirect("/")
    else:
        return render_template("myAccount.html", signedIn = loginStatus(), error=error, username = getUsername())


@app.route("/signup", methods=["POST"])
def signup_post():
    username = request.form["username"]
    password = request.form["password"]
    rePassword = request.form["rePassword"]

    valid = True
    error = "none"

    #check if any instance of the new username exists within the database
    conn = sqlite3.connect(usersDB)
    cursor = conn.cursor()
    cursor.execute(""" SELECT username FROM users WHERE username=(?) COLLATE NOCASE""", (username,))
    result = cursor.fetchone()
    cursor.close()

    if result or username == "":
        valid = False
        error = "Username aready exists! Did you mean to log in?"
    else:
        if password != rePassword:
            valid = False
            error = "Passwords do not match!"

    if valid:
        securePassword = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        cursor = conn.cursor()
        cursor.execute("""INSERT INTO users VALUES (?, ?)""", (username, securePassword))
        conn.commit()
        cursor.close()

        return redirect("/login")
    else:
        return render_template("signup.html", signedIn = loginStatus(), error=error, username = getUsername())

@app.route("/login", methods = ["POST"])
def login_post():
    username = request.form["username"]
    password = request.form["password"]

    valid = True

    if username != "":
        #try...except to catch usernames that do not exist in the db
        try:
            conn = sqlite3.connect(usersDB)
            cursor = conn.cursor()
            cursor.execute(""" SELECT password FROM users WHERE username=(?)""", (username,))
            dbPassword = cursor.fetchone()[0]
            cursor.close()

            if dbPassword != bcrypt.hashpw(password.encode("utf8"), dbPassword):
                valid = False
        except:
            valid = False

    else:
        valid = False

    if valid:
        session["username"] = username
        session["logged"] = True
        return redirect("/")
    else:
        error = "Username or Password Incorrect!"
        return render_template("login.html", signedIn = loginStatus(), error=error, username = getUsername())

@app.route("/delete-confirm", methods=["POST"])
def deleteConfirm_post():
    conn = sqlite3.connect(listingsDB)
    cursor = conn.cursor()
    cursor.execute(""" DELETE FROM listings WHERE seller=(?)""", (getUsername(),))
    conn.commit()
    cursor.close()

    conn = sqlite3.connect(usersDB)
    cursor = conn.cursor()
    cursor.execute(""" DELETE FROM users WHERE username=(?)""", (getUsername(),))
    conn.commit()
    cursor.close()

    return redirect("/logout")

@app.route("/edit-listing-<number>", methods=["POST"])
def listingEdit_post(number):
    newTitle = request.form["title"]
    newPlatform = request.form["platform"]
    newPrice = request.form["price"]

    valid = True
    error = "none"

    if newTitle == "":
        valid = False
        error = "No title entered!"
    else:
        # Check if a valid platform has been selected.
        platformSelected = False
        for platform in platforms:
            if newPlatform == platform:
                platformSelected = True

        if not platformSelected:
            valid = False
            error = "Invalid Platform! Use the dropdown menu to select the platform."
        else:
            # Check if a numerical value has been entered for price
            try:
                decimalPrice = Decimal(newPrice)
                decimalPrice += 1
                if not len(newPrice.rsplit(".")[-1]) == 2:
                    valid = False
                    error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"
            except:
                valid = False
                error = "Invalid Price! Ensure price is in the format £££.pp. (EG/ 7.00)"

    conn = sqlite3.connect(listingsDB)
    if valid:
        cursor = conn.cursor()
        cursor.execute("""UPDATE listings SET game=(?), platform=(?), price=(?) WHERE id=(?)""",
        (newTitle, newPlatform, newPrice, number,))
        conn.commit()
        cursor.close()

        return redirect("/")
    else:
        cursor = conn.cursor()
        cursor.execute(""" SELECT game, platform, price FROM listings WHERE id=(?)""", (number,))
        currentInfo = cursor.fetchone()
        cursor.close()

        return render_template("newListing.html", signedIn = loginStatus(), platforms=platforms, pageTitle="Edit Listing", error = error,
        username = getUsername(), currentTitle = currentInfo[0], currentPlatform = currentInfo[1], currentPrice= currentInfo[2])
