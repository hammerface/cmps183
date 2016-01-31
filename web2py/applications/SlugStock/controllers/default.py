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
    #onvalidation = yahoo --- in form.process
    if form.process().accepted:
        response.flash = 'following new ticker'
    following = db(db.following.u_id==auth.user_id).select()
    #listoftickers
    #for follow in following:
    #    listoftickers.add db(db.recent.ticker==follow.ticker).select()
    #following = db().select(db.following.ALL)
    #query = ((db.following.u_id==auth.user_id))
    #grid = SQLFORM.grid(query, user_signature=True, editable=False, create=False, csv=False)
    return dict(form=form, following=following)

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
