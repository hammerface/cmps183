# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

#def email_trevor():
#    following = db(db.following).select()
#    for follow in following:
#        mail = auth.settings.mailer
#        mail.settings.server = 'smtp.gmail.com:587'
#        mail.settings.sender = 'ucscstock@gmail.com'
#        mail.settings.login = 'ucscstock@gmail.com:julligjullig'
#        mail.send('pbgreerb@ucsc.edu', 'Message subject', 'Plain text body of the message')

import urllib2
import re
import datetime
import csv
import urllib2

#takes in string containing the ticker name

def csv_read(ticker):
    url = "http://ichart.finance.yahoo.com/table.csv?s=" + ticker
    #url = "http://ichart.finance.yahoo.com/table.csv?s=AAPL&a=01&b=11&c=2016&d=01&e=14&f=2016&g=d&ignore=.csv"
    response = urllib2.urlopen(url)
    cr = csv.reader(response)
    first = True
    for row in cr:
        if first:
            first = False
            continue
        db.historic.insert(ticker=ticker,
                            Date=row[0],
                            Open=row[1],
                            High=row[2],
                            Low=row[3],
                            Close=row[4],
                            Volume=row[5],
                            Adj=row[6])

def index():
    return dict()

def getYahooPrice(ticker):
    htmlfile = urllib2.urlopen("http://finance.yahoo.com/q?s="+ticker)
    htmltext = htmlfile.read()
    regex = '<span id="yfs_l84_'+ticker+'">(.+?)</span>'
    pattern = re.compile(regex)
    price = re.findall(pattern,htmltext)
    try:
        priceFloat = float(price[0])
        print priceFloat
        return priceFloat
    except IndexError as e:
        print 'invalid ticker'
        return None

def validateTicker(form):
    #check that they are not already following this stock
    print '================='
    query = db.following.id > 0
    query &= db.following.u_id==auth.user_id
    query &= db.following.ticker==form.vars.ticker
    alreadyFollowing = db(query).select().first()
    if (alreadyFollowing != None):
        form.errors.ticker = 'You are already following that stock.'
        return
    #check in database
    print form.vars.ticker
    ticker = db(db.recent.ticker == form.vars.ticker).select().first()

    if ticker != None:
        print 'found in database'
        print ticker.price
    else:
        #call yahoo
        print 'not found in database, calling yahoo'
        yahooPrice = getYahooPrice(form.vars.ticker)
        if yahooPrice != None:
            #get recent price and put in recent table
            print yahooPrice
            db.recent.insert(ticker=form.vars.ticker,
                             price=yahooPrice,
                             datetime=datetime.datetime.today())
            #get csv file and put in historic table
            csv_read(form.vars.ticker)
        else:
            form.errors.ticker = 'Stock not found.'


@auth.requires_login()
def profile():
    #
    recentPrices = db(db.recent.ticker!=None).select()
    for currRecent in recentPrices:
        htmlfile = urllib2.urlopen("http://finance.yahoo.com/q?s="+currRecent.ticker)
        htmltext = htmlfile.read()
        regex = '<span id="yfs_l84_'+currRecent.ticker+'">(.+?)</span>'
        pattern = re.compile(regex)
        newPrice = re.findall(pattern,htmltext)
        try:
            currRecent.update_record(price = float(newPrice[0]))
        except IndexError as e:
            currRecent.price = currRecent.price
    #
    form = SQLFORM(db.following)
    if form.accepts(request.vars, onvalidation = validateTicker):
        response.flash = 'following new ticker'
    following = db(db.following.u_id==auth.user_id).select()
    follow_list = []
    for follower in following:
        try:
            recent = db(db.recent.ticker == follower.ticker).select().first()
            follow_list.append((follower.ticker, recent.price, follower.id))
        except:
            follow_list.append((follower.ticker, 0, follower.id))
    return dict(form=form, following=follow_list)

@auth.requires_login()
def delete_follow():
    id = request.args(0)
    remove = db(db.following.id==id).delete()
    if remove:
        redirect(URL('profile'))
    return dict(remove=remove)

def user():
    return dict(form=auth())


@cache.action()
def download():
    return response.download(request, db)


def call():
    return service()
