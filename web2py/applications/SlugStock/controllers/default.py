# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

import urllib2
import re
import datetime
import csv

from gluon.contrib.sms_utils import SMSCODES, sms_email
"""
def text_me(phone, provider):
    mail = auth.settings.mailer
    mail.settings.server = 'smtp.gmail.com:587'
    mail.settings.sender = 'ucscstock@gmail.com'
    mail.settings.login = 'ucscstock@gmail.com:julligjullig'
    phone = '925-683-6184'
    provider = 'AT&T'
    email = sms_email(phone, provider)
    mail.send(to=email, subject='Hello', message='Goodbye')
"""

def csv_daily():
    # gets unique tickers
    tickers = db(db.historic.id > 0).select(db.historic.ticker, distinct=True)

    #month, day, year
    date = datetime.date.today()
    month = str(date.month - 1)
    day = str(date.day)
    year = str(date.year)
    if len(month) < 2:
        month = "0" + month
    if len(day) < 2:
        day = "0" + day

    urlend = ("&a=" + month + "&b=" + "2" + "&c=" + year
               + "&d=" + month + "&e=" + "2" + "&f=" + year
               + "&g=d&ignore=.csv")

    for row in tickers:
        i = 1
        try:
            url = "http://real-chart.finance.yahoo.com/table.csv?s=" + row.ticker + urlend
            print url
            response = urllib2.urlopen(url)
            cr = csv.reader(response)
            for rowcr in cr:
                if i == 1:
                    i = 2
                    continue
                alreadyin = db((db.historic.ticker==row.ticker) & (db.historic.Date==rowcr[0])).select().first()
                if alreadyin != None:
                    print "Its already in the database"
                    break
                db.historic.insert(ticker=row.ticker,
                                Date=rowcr[0],
                                Open=rowcr[1],
                                High=rowcr[2],
                                Low=rowcr[3],
                                Close=rowcr[4],
                                Volume=rowcr[5],
                                Adj=rowcr[6])
                i = i + 1
        except urllib2.HTTPError:
            print 'historic stock info not found'
        if i == 2:
            print 'there was no new stock info'



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
#    alreadyFollowing = False
#    currentlyFollowing = db(db.following.u_id == auth.user_id).select()
#    for follow in currentlyFollowing:
#        if follow.ticker == forms.vars.ticker:
#            alreadyFollowing = True
#    if (alreadyFollowing == True):
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
            scheduler.queue_task('csv_read', [form.vars.ticker])
            #csv_read(form.vars.ticker)
        else:
            form.errors.ticker = 'Stock not found.'

def validateSubscription(form):
    query = db.following.id > 0
    query &= db.following.u_id==auth.user_id
    query &= db.following.ticker==form.vars.ticker
    alreadyFollowing = db(query).select().first()
    if (alreadyFollowing == None):
        form.errors.ticker = 'You are not following that stock.'
        return

#maybe make this index()
@auth.requires_login()
def profile():
    csv_daily()
    #text_me(None, None)
    followForm = SQLFORM(db.following)
    if followForm.accepts(request.vars, onvalidation = validateTicker):
        response.flash = 'following new ticker'
    subscriptionForm = SQLFORM(db.subscription)
    if subscriptionForm.accepts(request.vars, onvalidation = validateSubscription):#do proper validation for following
        response.flash = 'subscribed to new ticker'
    following = db(db.following.u_id==auth.user_id).select()
    follow_list = []
    for follower in following:
        try:
            recent = db(db.recent.ticker == follower.ticker).select().first()
            query = db.subscription.u_id == auth.user_id
            query &= db.subscription.ticker == follower.ticker
            subscriptions = db(query).select()
            follow_list.append((follower.ticker, recent.price, subscriptions, follower.id))
        except:
            follow_list.append((follower.ticker, 0, follower.id))
    return dict(followForm=followForm, subscriptionForm=subscriptionForm, following=follow_list)

@auth.requires_login()
def delete_follow():
    id = request.args(0)
    remove = db(db.following.id==id).delete()
    if remove:
        redirect(URL('profile'))
    return dict(remove=remove)

@auth.requires_login()
def delete_subscription():
    id = request.args(0)
    remove = db(db.subscription.id==id).delete()
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
