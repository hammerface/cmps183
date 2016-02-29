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
    ticker = db(db.current.ticker == form.vars.ticker).select().first()

    if ticker != None:
        print 'found in database'
        print ticker.price
    else:
        #call yahoo
        print 'not found in database, calling yahoo'
        yahooPrice = getYahooPrice(form.vars.ticker)
        if yahooPrice != None:
            #get current price and put in current table
            print yahooPrice
            db.current.insert(ticker=form.vars.ticker,
                             price=yahooPrice,
                             datetime=datetime.datetime.today())
            db.recent.insert(ticker=form.vars.ticker,
                             price=yahooPrice,
                             datetime=datetime.datetime.today())
            #get csv file and put in historic table
            csv_read(form.vars.ticker)
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
    worth = 0
    followForm = SQLFORM(db.following)
    if followForm.accepts(request.vars, onvalidation = validateTicker):
        response.flash = 'following new ticker'
    subscriptionForm = SQLFORM(db.subscription)
    if subscriptionForm.accepts(request.vars, onvalidation = validateSubscription):#do proper validation for following
        response.flash = 'subscribed to new ticker'
    noteForm = SQLFORM(db.note)
    if noteForm.accepts(request.vars, onvalidation = validateSubscription):#do proper validation for following
        response.flash = 'new note added to ticker'
    following = db(db.following.u_id==auth.user_id).select()
    follow_list = []
    for follower in following:
        try:
            recent = db(db.recent.ticker == follower.ticker).select().first()
            worth += follower.owned * recent.price
            querySub = db.subscription.u_id == auth.user_id
            querySub &= db.subscription.ticker == follower.ticker
            queryNote = db.note.u_id == auth.user_id
            queryNote &= db.note.ticker == follower.ticker
            subscriptions = db(querySub).select()
            notes = db(queryNote).select()
            follow_list.append((follower.ticker, recent.price, subscriptions, follower.id, notes, follower.owned))
        except:
            follow_list.append((follower.ticker, 0, follower.id))
    user = db(db.auth_user.id==auth.user_id).select().first()
    user.update_record(netWorth=worth)
    db.commit()
    return dict(followForm=followForm, subscriptionForm=subscriptionForm, following=follow_list, noteForm=noteForm, user=user)

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

@auth.requires_login()
def delete_note():
    id = request.args(0)
    remove = db(db.note.id==id).delete()
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
