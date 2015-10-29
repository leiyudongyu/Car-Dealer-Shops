from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, DealerShop, Cars, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Car Dealer Shop Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///cardealershop.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
 
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Google DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# Facsbook disconnect
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"



# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showShops'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showShops'))

@app.route('/')
@app.route('/cardealershop/')
def showShops():
    carshops = session.query(DealerShop).order_by(asc(DealerShop.name))
    if 'username' not in login_session:
        return render_template('publiccarshops.html', carshops = carshops)
    else:
        return render_template('carshops.html', carshops = carshops)


@app.route('/cardealershop/new/', methods=['GET', 'POST'])
def newCarShop():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newShop = DealerShop(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newShop)
        flash('New DealerShop %s Successfully Created' % newShop.name)
        session.commit()
        return redirect(url_for('showShops'))
    else:
        return render_template('newCarShop.html')

@app.route('/cardealershop/<int:carshop_id>/')
@app.route('/cardealershop/<int:carshop_id>/car/')
def showCars(carshop_id):
    carshop = session.query(DealerShop).filter_by(id=carshop_id).one()
    creator = getUserInfo(carshop.user_id)
    items = session.query(Cars).filter_by(
        shop_id = carshop_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiccars.html', items=items, carshop=carshop, creator=creator)
    else:
        return render_template('cars.html', items=items, carshop = carshop, creator=creator)


@app.route('/cardealershop/<int:carshop_id>/edit/', methods=['GET', 'POST'])
def editCarShop(carshop_id):
    editedCarShop = session.query(
        DealerShop).filter_by(id=carshop_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCarShop.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCarShop.name = request.form['name']
            flash('Car Shop %s Successfully Edited' % editedCarShop.name)
            return redirect(url_for('showCars', carshop_id = carshop_id))
    else:
        return render_template('editCarShop.html', carshop = editedCarShop)


@app.route('/cardealershop/<int:carshop_id>/delete/', methods=['GET', 'POST'])
def deleteCarShop(carshop_id):
    carShopToDelete = session.query(
        DealerShop).filter_by(id=carshop_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if carShopToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(carShopToDelete)
        flash('%s Successfully Deleted' % carShopToDelete.name)
        session.commit()
        return redirect(url_for('showShops'))
    else:
        return render_template('deleteCarShop.html', carshop = carShopToDelete)

@app.route('/cardealershop/<int:carshop_id>/menu/new/', methods=['GET', 'POST'])
def newCar(carshop_id):
    if 'username' not in login_session:
        return redirect('/login')
    carshop = session.query(DealerShop).filter_by(id=carshop_id).one()
    if login_session['user_id'] != carshop.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add menu items to this restaurant. Please create your own restaurant in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        car = Cars(name=request.form['name'], description=request.form['description'], price=request.form['price'], course=request.form['course'], shop_id=carshop_id, user_id=carshop.user_id)
        session.add(car)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (car.name))
        return redirect(url_for('showCars', carshop_id=carshop_id))
    else:
        return render_template('newcars.html', carshop_id=carshop_id)

@app.route('/cardealershop/<int:carshop_id>/car/<int:car_id>/edit', methods=['GET', 'POST'])
def editCar(carshop_id, car_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedCar = session.query(Cars).filter_by(id=car_id).one()
    carshop = session.query(DealerShop).filter_by(id=carshop_id).one()
    if login_session['user_id'] != carshop.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit menu items to this restaurant. Please create your own restaurant in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedCar.name = request.form['name']
        if request.form['description']:
            editedCar.description = request.form['description']
        if request.form['price']:
            editedCar.price = request.form['price']
        if request.form['course']:
            editedCar.course = request.form['course']
        session.add(editedCar)
        session.commit()
        flash('Car Successfully Edited')
        return redirect(url_for('showCars', carshop_id = carshop_id))
    else:
        return render_template('editcar.html', carshop_id = carshop_id, car_id = car_id, item = editedCar)

@app.route('/cardealershop/<int:carshop_id>/car/<int:car_id>/delete', methods=['GET', 'POST'])
def deleteCar(carshop_id, car_id):
    if 'username' not in login_session:
        return redirect('/login')
    carshop = session.query(DealerShop).filter_by(id=carshop_id).one()
    carToDelete = session.query(Cars).filter_by(id=car_id).one()
    if login_session['user_id'] != carshop.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete menu items to this restaurant. Please create your own restaurant in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(carToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCars', carshop_id = carshop_id))
    else:
        return render_template('deleteCar.html', item = carToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)



