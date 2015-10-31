# Car-Dealer-Shops

This is one of the web projects of Full Stack Web Developer Nanodegree in Udacity.

In this project, I wrote sql scheme, built an web server using flask framwork of python and using SQLalchemy API to connect the sqlite database. I made a Restfull web application which can provide HTTP related CRUD methods handling a list of car shops and its cars. JSON APIs are also provided for data query. Then I implement third pary OAuth authentication for car shops and cars management. 

- Skills: Google+ API, Facebook SDK, Restfull API SQLalchemy API, Sqlite Database, Python, Javascript, Ajax, HTML, CSS, Json

Features: <br/>
1. Using Flask ( a light Python web framework).<br/>
2. Using OAuth 2.0 to access Google APIs and Facebook API using google or facebook account.<br/>
3. Using RESRfull APIs, like Post and Get.<br/>
4. Providing JSON APIs, which you can exploit to get the information you want.<br/>

How to run:<br/>
1. Run database_setup.py to create restaurantmenu.db<br/>
2. Run __init__.py to connect the sqlite database and webserver<br/>
3. Go to http://localhost:5000/ and you will see the page as below<br/>

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/21.jpg)

You can choose each carshop and find their cars as below:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/22.jpg)

Because you are not login, so you can not create or delete or edit carshops and cars, and there are no such buttons showing on the page.

If you are the user, you can click log in options on the top-right corner of the page, then you can choose using Google+ or Facebook to login.

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/23.jpg)

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/24.jpg)

Then you can see you are now log in as (your name) and a Add car shop button shows:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/25.jpg)

You can click it and add car shop, then a new car shop cooresponding to your user_id will be created, and you can manipulate its cars by click the shop's name:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/26.jpg)

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/27.jpg)

Comparing with non-login page, you can see there are more buttons on the page which can let you manipulate your car shop and its cars.

Changing car shop's name:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/28.jpg)

Adding car:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/29.jpg)

Delete car shop:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/30.jpg)

For each car, you can edit, delete too:

Edit car:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/31.jpg)

Delete car:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/32.jpg)

If you want to log out, you can click the log out button on the right-top of the page, then you can see you have been log out:

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/33.jpg)

You can use JSON APIs like: 

![image](https://raw.githubusercontent.com/leiyudongyu/images/master/34.jpg)
