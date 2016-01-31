# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

def index():
    return dict()

@auth.requires_login()
def profile():
    form = SQLFORM(db.following)
    if form.process().accepted:
        response.flash = 'following new ticker'
    following = db().select(db.following.u_id==auth.user_id)
    #query = ((db.following.u_id==auth.user_id))
    #grid = SQLFORM.grid(query, user_signature=True, editable=False, create=False, csv=False)
    return dict(form=form, following=following)

def user():
    return dict(form=auth())


@cache.action()
def download():
    return response.download(request, db)


def call():
    return service()


