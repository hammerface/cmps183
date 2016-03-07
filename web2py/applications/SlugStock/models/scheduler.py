# -*- coding: utf-8 -*-
import urllib2
import re
import datetime

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



def csv_read(ticker):
    url = "http://ichart.finance.yahoo.com/table.csv?s=" + ticker
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

def emergency_email(email, ticker, label, limit):
    mail = auth.settings.mailer
    mail.settings.server = 'smtp.gmail.com:587'
    mail.settings.sender = 'ucscstock@gmail.com'
    mail.settings.login = 'ucscstock@gmail.com:julligjullig'
    title = 'Slug Stock: STOCK UPDATE FOR ' + ticker
    body = ticker + '\'s price has ' + label + ' the price limit you set of ' + str(limit)
    mail.send(email, title , body)

def updateYahooPrices():
    recentPrices = db(db.recent.ticker!=None).select()
    for currRecent in recentPrices:
        htmlfile = urllib2.urlopen("http://finance.yahoo.com/q?s="+currRecent.ticker)
        htmltext = htmlfile.read()
        regex = '<span id="yfs_l84_'+currRecent.ticker+'">(.+?)</span>'
        pattern = re.compile(regex)
        newPrice = re.findall(pattern,htmltext)
        try:
            subscriptions = db(db.subscription.ticker==currRecent.ticker).select()
            for currSub in subscriptions:
                user = db(db.auth_user.id==currSub.u_id).select().first()
                email = user.email
                phone_email = sms_email(user.phone_number, user.phone_provider)
                if currRecent.price < currSub.value and currSub.value < float(newPrice[0]):
                    scheduler.queue_task('emergency_email', [email, currSub.ticker, 'risen above', currSub.value])
                    scheduler.queue_task('emergency_email', [phone_email, currSub.ticker, 'risen above', currSub.value])
                    db(db.subscription.id==currSub.id).delete()
                elif currRecent.price > currSub.value and currSub.value > float(newPrice[0]):
                    scheduler.queue_task('emergency_email', [email, currSub.ticker, 'fallen below', currSub.value])
                    db(db.subscription.id==currSub.id).delete()
            currRecent.update_record(price=float(newPrice[0]))
            db.commit()
        except IndexError as e:
            i = 1#do nothing

def email_trevor():
    mail = auth.settings.mailer
    mail.settings.server = 'smtp.gmail.com:587'
    mail.settings.sender = 'ucscstock@gmail.com'
    mail.settings.login = 'ucscstock@gmail.com:julligjullig'
    mail.send('jrbrower@ucsc.edu', 'Message subject', 'Plain text body of the message')

def email_daily():
    users = db(db.auth_user).select()
    for user in users:
        following = db(db.following.u_id==user.id).select()
        follow_list = []
        if following:
            for stock in following:
                recent = db(db.recent.ticker == stock.ticker).select().first()
                follow_list.append((recent.ticker, recent.price))
            follow_string = "Hello, " + user.first_name + ". Here are the closing prices of the stocks you are currently following: \n"
            for x in follow_list:
                follow_string += "Ticker: " + x[0] + " Closing Price: " + str(x[1]) + "\n"
            mail = auth.settings.mailer
            mail.settings.server = 'smtp.gmail.com:587'
            mail.settings.sender = 'ucscstock@gmail.com'
            mail.settings.login = 'ucscstock@gmail.com:julligjullig'
            mail.send(to=user.email,
                      subject='Your Daily Stock Information Courtesy of SlugStock',
                      message=(follow_string))

from gluon.scheduler import Scheduler
scheduler = Scheduler(db, tasks=dict(email=email_trevor, updatePrices=updateYahooPrices, emergency_email=emergency_email, email_daily=email_daily, csv_read=csv_read, csv_daily=csv_daily))
