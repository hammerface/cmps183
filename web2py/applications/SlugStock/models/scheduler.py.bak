# -*- coding: utf-8 -*-
import urllib2
import re
import datetime
import csv

from gluon.contrib.sms_utils import SMSCODES, sms_email

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

def remove_completed_tasks():
    completedTasks = db(db.scheduler_task.status=="COMPLETED").delete()
    db.commit()

def emergency_email(email, ticker, label, limit):
    mail = auth.settings.mailer
    mail.settings.server = 'smtp.gmail.com:587'
    mail.settings.sender = 'ucscstock@gmail.com'
    mail.settings.login = 'ucscstock@gmail.com:julligjullig'
    title = 'Slug Stock: STOCK UPDATE FOR ' + ticker
    body = ticker + '\'s price has ' + label + ' the price limit you set of ' + str(limit)
    mail.send(email, title , body)

def updateYahooPrices():
    currentPrices = db(db.current.ticker!=None).select()
    for currPrice in currentPrices:
        htmlfile = urllib2.urlopen("http://finance.yahoo.com/q?s="+currPrice.ticker)
        htmltext = htmlfile.read()
        regex = '<span id="yfs_l84_'+currPrice.ticker+'">(.+?)</span>'
        pattern = re.compile(regex)
        newPrice = re.findall(pattern,htmltext)
        db.recent.insert(ticker=currPrice.ticker,
                         price=float(newPrice[0]),
                         day=db(db.day.day!=None).select().first().day,
                         datetime=datetime.datetime.today())
        try:
            subscriptions = db(db.subscription.ticker==currPrice.ticker).select()
            for currSub in subscriptions:
                user = db(db.auth_user.id==currSub.u_id).select().first()
                email = user.email
                phone_email = sms_email(user.phone_number, user.phone_provider)
                if currPrice.price < currSub.value and currSub.value < float(newPrice[0]):
                    scheduler.queue_task('emergency_email', [email, currSub.ticker, 'risen above', currSub.value])
                    scheduler.queue_task('emergency_email', [phone_email, currSub.ticker, 'risen above', currSub.value])
                    db(db.subscription.id==currSub.id).delete()
                elif currPrice.price > currSub.value and currSub.value > float(newPrice[0]):
                    scheduler.queue_task('emergency_email', [email, currSub.ticker, 'fallen below', currSub.value])
                    db(db.subscription.id==currSub.id).delete()
            currPrice.update_record(price=float(newPrice[0]))
            db.commit()
        except IndexError as e:
            i = 1#do nothing

def email_trevor():
    mail = auth.settings.mailer
    mail.settings.server = 'smtp.gmail.com:587'
    mail.settings.sender = 'ucscstock@gmail.com'
    mail.settings.login = 'ucscstock@gmail.com:julligjullig'
    mail.send('twbarne@ucsc.edu', 'Message subject', 'Plain text body of the message')


def email_daily():
    users = db(db.auth_user).select()
    for user in users:
        following = db(db.following.u_id==user.id).select()
        follow_list = []
        if following:
            worth = 0
            for stock in following:
                current = db(db.current.ticker == stock.ticker).select().first()
                worth += stock.owned * current.price
                follow_list.append((current.ticker, current.price))
            net_worth_change = worth - user.netWorth
            follow_string = "Hello, " + user.first_name + ". Your current net worth is $" + str(worth) + ", which is a $" + str(net_worth_change) + " change from when you last checked. \n Here are the closing prices of the stocks you are currently following: \n"
            for x in follow_list:
                follow_string += "Ticker: " + x[0] + " Closing Price: " + str(x[1]) + "\n"
            mail = auth.settings.mailer
            mail.settings.server = 'smtp.gmail.com:587'
            mail.settings.sender = 'ucscstock@gmail.com'
            mail.settings.login = 'ucscstock@gmail.com:julligjullig'
            mail.send(to=user.email,
                      subject='Your Daily Stock Information Courtesy of SlugStock',
                      message=(follow_string))

def nextday():
    day = db(db.day.day!=None).select().first()
    day.update_record(day=(day.day + 1))
    db(db.recent.day<=(day.day-5)).delete()
    db.commit()

from gluon.scheduler import Scheduler
scheduler = Scheduler(db, tasks=dict(email=email_daily, updatePrices=updateYahooPrices, emergency_email=emergency_email, clear=remove_completed_tasks, nextday=nextday, csv_read=csv_read, csv_daily=csv_daily))
