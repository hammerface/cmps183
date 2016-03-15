from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)

db = DAL("sqlite://storage.sqlite", migrate=True)#migrate=True fake_migrate=True

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

auth.settings.extra_fields['auth_user']= [
   Field('phone_number', 'string', requires = IS_MATCH('^\d{3}-?\d{3}-?\d{4}$', error_message='example: 111-555-2345')),
   Field('phone_provider', 'string', requires = IS_IN_SET(('AT&T','Metro PCS','Sprint PCS', 'T-Mobile USA (tmail)', 'Verizon Wireless (vtext)', 'Virgin Mobile USA'))),
   Field('daily_message', 'boolean', default=False),
   Field('get_texts', 'boolean', default=False),
   Field('netWorth', 'double', writable=False,)
   ]
## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.server')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

auth.settings.login_next = URL('profile')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
#auth.enable_record_versioning(db)

db.define_table('historic',
   Field('ticker', 'string'),
   Field('Date', 'date'),
   Field('Open', 'double'),
   Field('High', 'double'),
   Field('Low', 'double'),
   Field('Close', 'double'),
   Field('Volume', 'integer'),
   Field('Adj', 'double')
   )

db.historic.ticker.requires = IS_NOT_EMPTY()
db.historic.Date.requires = IS_DATE()
db.historic.Open.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)
db.historic.High.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)
db.historic.Low.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)
db.historic.Close.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)
db.historic.Volume.requires = IS_INT_IN_RANGE(0, 1e100)
db.historic.Adj.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)

db.define_table('current',
   Field('ticker', 'string'),
   Field('datetime', 'date'),
   Field('price', 'double', writable=True),
   )

db.current.ticker.requires = IS_NOT_EMPTY()
db.current.datetime.requires = IS_DATE()
db.current.price.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)

db.define_table('recent',
   Field('ticker', 'string'),
   Field('datetime', 'datetime', default=request.now),
   Field('day', 'integer'),
   Field('price', 'double'),
   )

db.recent.ticker.requires = IS_NOT_EMPTY()
db.recent.datetime.requires = IS_DATETIME()
db.recent.day.requires = IS_INT_IN_RANGE(0, 1e100)
db.recent.price.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)

db.define_table('following',
   Field('u_id', 'reference auth_user', default=auth.user_id, readable=False, writable=False),
   Field('ticker', 'string'),
   Field('owned', 'integer', default=0)
   )

db.following.ticker.requires = IS_NOT_EMPTY()
db.following.owned.requires = IS_INT_IN_RANGE(0, 1e100)

db.define_table('subscription',
   Field('u_id', 'reference auth_user', default=auth.user_id, readable=False, writable=False),
   Field('ticker', 'string'),
   Field('value', 'double')
   )

db.define_table('note',
   Field('u_id', 'reference auth_user', default=auth.user_id, readable=False, writable=False),
   Field('ticker', 'string'),
   Field('note', 'string')
   )

db.subscription.ticker.requires = IS_NOT_EMPTY()
db.subscription.value.requires = IS_FLOAT_IN_RANGE(-1e100, 1e100)

db.define_table('day',
   Field('day', 'integer', default=0)
   )

######################################################################
