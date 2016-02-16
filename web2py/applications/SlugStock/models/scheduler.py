# -*- coding: utf-8 -*-
import urllib2
import re
import datetime

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
                email = db(db.auth_user.id==currSub.u_id).select().first().email
                if currRecent.price < currSub.value and currSub.value < float(newPrice[0]):
                    scheduler.queue_task('emergency_email', [email, currSub.ticker, 'risen above', currSub.value])
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
scheduler = Scheduler(db, tasks=dict(email=email_trevor, updatePrices=updateYahooPrices, emergency_email=emergency_email, email_daily=email_daily))
