# -*- coding: utf-8 -*-
import urllib2
import re
import datetime

def updateYahooPrices():
    recentPrices = db(db.recent.ticker!=None).select()
    for currRecent in recentPrices:
        currRecent.price = 1.0
        htmlfile = urllib2.urlopen("http://finance.yahoo.com/q?s="+currRecent.ticker)
        htmltext = htmlfile.read()
        regex = '<span id="yfs_l84_'+currRecent.ticker+'">(.+?)</span>'
        pattern = re.compile(regex)
        newPrice = re.findall(pattern,htmltext)
        try:
            currRecent.update_record(price=float(newPrice[0]))
            db.commit()
        except IndexError as e:
            i = 1

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
        for stock in following:
            recent = db(db.recent.ticker == stock.ticker).select().first()
            follow_list.append((recent.ticker, recent.price))
        follow_string = ("\n".join("Ticker: " ++ str(x[0]) ++ "Closing Price: ") for x in follow_list)
        mail = auth.settings.mailer
        mail.send(to=user.email,
                  subject='Your Daily Stock Information',
                  message=('Here are the closing prices of the stocks you are currently following: %s', follow_string))

from gluon.scheduler import Scheduler
scheduler = Scheduler(db, tasks=dict(email=email_trevor, updatePrices=updateYahooPrices))
