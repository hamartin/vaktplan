#!/usr/bin/env python
# coding: latin1


'''
Vaktplan is a calendar meant to be used by me privately. It supports
basic authentication, adding and removing comments on specific dates.

Syntax to create the database needed to run the application.

sqlite> create table vaktplan (comment text, date text, cdate date);
sqlite> create trigger insert_date_created after insert on vaktplan
    ...> begin
    ...> update vaktplan set cdate = datetime('now')
    ...> where rowid = new.rowid;
    ...> end;
sqlite>
sqlite> create table users (user text, password text, cdate date);
sqlite> create trigger insert_date_user_created after insert on users
    ...> begin
    ...> update users set cdate = datetime('now')
    ...> where rowid = new.rowid;
    ...> end;
sqlite>
'''


import calendar
import datetime
import hashlib
import web

from sqlite3 import OperationalError
from web import form


#
# Settings / Config
#


DEBUG = False
AUTORELOAD = False

DBTYPE = 'sqlite'
DBFILENAME = 'vaktplan.db'
DBTABLE = 'vaktplan'
USERTABLE = 'users'
TEMPLATEFOLDER = 'templates/'
SESSIONSFOLDER = 'sessions/'


#
# Statics
#


URLS = (
    '/changepass/', 'Changepass', '/changepass', 'Changepass',
    '/login/', 'Login', '/login', 'Login',
    '/logout/', 'Logout', '/logout', 'Logout',
    '/ym/d/del/', 'Del', '/ym/d/del', 'Del',
    '/ym/d/add/', 'Add', '/ym/d/add', 'Add',
    '/ym/d/', 'Day', '/ym/d', 'Day',
    '/ym/', 'Ym', '/ym', 'Ym',
    '/', 'Index',
)
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
                    'August', 'October', 'September', 'November', 'December')
DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                                                                    'Sunday')
APP = web.application(URLS, globals(), autoreload=AUTORELOAD)
STORE = web.session.DiskStore(SESSIONSFOLDER)
SESSION = web.session.Session(APP, STORE,
                    initializer={'loggedin': False, 'username': 'anonymous'})
RENDER = web.template.render(TEMPLATEFOLDER, base='layout',
                                                globals={'context': SESSION})
web.config.debug = DEBUG


#
# Functions
#


def notfound():
    ''' Returns custom 404 page. This function is intended to be hooked
    into web.py's running application's notfound method. '''
    return web.notfound(RENDER.notfound())


def loggedin():
    ''' Returns True if logged in and user is not anonymous, else False. '''
    if SESSION.username == 'anonymous' or SESSION.loggedin is False:
        return False
    else:
        return True


def gethash(inputstring):
    ''' Returns input string as a hashed sha256 hex digest. '''
    cshash = hashlib.sha256()
    cshash.update(inputstring)
    return cshash.hexdigest()


def updatepassword(username, password):
    ''' Updates a users password in the database. '''

    dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
    trans = dbh.transaction()
    try:
        dbh.update(USERTABLE, where='user="{0}"'.format(username),
                                        password='{0}'.format(password))
    except:
        trans.rollback()
        raise web.internalerror()
    else:
        trans.commit()


#
# Classes
#


class NoComment(Exception):

    ''' Exception class to use when a user tries to add an empty
    comment to the database. '''

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return repr("NoComment: {0}".format(self.msg))


class Index:

    ''' Shows the index page. '''

    def __init__(self):
        self.year = int(datetime.date.today().year)
        self.month = int(datetime.date.today().month) - 1
        self.day = int(datetime.date.today().day)

    def __str__(self):
        return repr("Index: {0}.{1}.{2}".format(self.day, self.month,
                                                                self.year))

    def GET(self):
        ''' Returns the index page. '''
        if loggedin():
            return RENDER.index(MONTHS, self.year, self.month)
        else:
            raise web.seeother('/login')

    def POST(self):
        ''' Dummy, forwards the user to /. '''
        if loggedin():
            raise web.seeother('/')
        else:
            raise web.seeother('/login')


class Ym:

    ''' Shows the "month" page. '''

    def __init__(self):

        i = web.input()
        cal = calendar.Calendar(0)

        try:
            self.year = int(i.year)
            self.month = int(i.month)
        except:
            raise web.seeother('/')
        else:
            if(self.year < 1990 or self.year > 2020 or self.month < 0 or
                                                            self.month > 11):
                raise web.notfound()

        self.yearin = int(datetime.date.today().year)
        self.monthin = int(datetime.date.today().month)
        self.dayin = int(datetime.date.today().day)

        self.dateslist = cal.monthdays2calendar(self.year, self.month + 1)

    def __str__(self):
        return repr("Ym: {0}.{1}".format(self.month, self.year))

    def GET(self):
        ''' Returns the month page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            return RENDER.ym(MONTHS, self.year, self.month, self.dateslist,
                                                    self.dayin, self.monthin)

    def POST(self):
        ''' Dummy, forwards the user to /. '''
        if loggedin():
            raise web.seeother('/')
        else:
            raise web.seeother('/login')


class Day:

    ''' Shows the "day" page. '''

    def __init__(self):

        i = web.input()

        try:
            self.year = int(i.year)
            self.month = int(i.month)
            self.day = int(i.day)
        except:
            raise web.seeother('/')
        else:
            if(self.year < 1990 or self.year > 2020 or self.month < 0 or
                    self.month > 11 or self.day < 1 or
                    self.day > calendar.monthrange(
                        self.year, self.month + 1)[1]):
                raise web.notfound()

        self.weekday = datetime.datetime.today().weekday()

    def __str__(self):
        return repr("Day: {0}.{1}.{2}".format(self.day, self.month, self.year))

    def GET(self):
        ''' Returns the day page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            rows = dbh.select(DBTABLE, what='comment,rowid',
                    where='date="{0}.{1}.{2}"'.format(
                        self.day, self.month, self.year))

            return RENDER.day(MONTHS, DAYS, self.year, self.month, self.day,
                    self.weekday, rows)

    def POST(self):
        ''' Dummy, forwards the user to /. '''
        if loggedin():
            raise web.seeother('/')
        else:
            raise web.seeother('/login')


class Add:

    ''' Adds data from page to database. '''

    def __init__(self):

        i = web.input()
        try:
            self.year = int(i.year)
            self.month = int(i.month)
            self.day = int(i.day)
            if i.comment == '':
                raise NoComment('No content.')
            self.comment = i.comment
        except NoComment:
            raise web.seeother('/ym/d/?year={0}&month={1}&day={2}'.format(
                                            self.year, self.month, self.day))
        except:
            raise web.seeother('/')
        else:
            if(self.year < 1990 or self.year > 2020 or self.month < 0 or
                    self.month > 11 or self.day < 1 or
                    self.month > calendar.monthrange(
                        self.year, self.month + 1)[1]):
                raise web.notfound()

    def __str__(self):
        return repr("Add: {0}.{1}.{2}".format(self.day, self.month, self.year))

    def GET(self):
        ''' Dummy, forwards to /. '''
        if loggedin():
            raise web.seeother('/')
        else:
            raise web.seeother('/login')

    def POST(self):
        ''' Stores data to the database and sends the user back to the
        same page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            trans = dbh.transaction()
            try:
                dbh.insert(DBTABLE, comment=self.comment,
                    date="{0}.{1}.{2}".format(self.day, self.month, self.year))
            except:
                trans.rollback()
                raise
            else:
                trans.commit()
            finally:
                raise web.seeother('/ym/d/?year={0}&month={1}&day={2}'.format(
                                            self.year, self.month, self.day))


class Del:

    ''' Deletes data from page to database. '''

    def __init__(self):

        i = web.input()
        try:
            self.rowid = int(i.id)
            self.year = int(i.year)
            self.month = int(i.month)
            self.day = int(i.day)
        except:
            raise web.seeother('/')
        else:
            if(self.year < 1990 or self.year > 2020 or self.month < 0 or
                    self.month > 11 or self.day < 1 or
                    self.day > calendar.monthrange(
                        self.year, self.month + 1)[1]):
                raise web.notfound()

    def __str__(self):
        return repr("Del: {0}.{1}.{2}".format(self.day, self.month, self.year))

    def GET(self):
        ''' Dummy, forwards to /. '''
        if loggedin():
            raise web.seeother('/')
        else:
            raise web.seeother('/login')

    def POST(self):
        ''' Deletes data from the database and sends the user back to
        the same page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            trans = dbh.transaction()
            try:
                dbh.delete(DBTABLE, where='rowid={0}'.format(self.rowid))
            except:
                trans.rollback()
                raise
            else:
                trans.commit()
            finally:
                raise web.seeother('/ym/d/?year={0}&month={1}&day={2}'.format(
                                            self.year, self.month, self.day))


class Login:

    ''' Class to deal with all things authentication and login pages. '''

    def __init__(self):
        self.login = form.Form(
                form.Textbox('username', form.notnull, description='Username'),
                form.Password('password', form.notnull,
                                                    description='Password'),
                form.Button('Login'))

    def GET(self):
        ''' Shows the login page. '''
        login = self.login()
        return RENDER.login(login)

    def POST(self):
        ''' Process the login credentials. '''

        login = self.login()
        if not login.validates():
            return RENDER.login(login)
        else:
            username = login['username'].value
            password = login['password'].value
            hpassword = gethash(password)

        try:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            rows = dbh.select(USERTABLE, what='password',
                                        where='user="{0}"'.format(username))
            dbupass = rows[0].password
        except IndexError:
            raise web.seeother('/login')
        except OperationalError:
            raise web.internalerror()

        if(hpassword == dbupass):
            SESSION.loggedin = True
            SESSION.username = username
            raise web.seeother('/')
        else:
            raise web.seeother('/login')


class Logout:

    ''' Class that handles logging users out of the system. '''

    def __init__(self):
        pass

    def GET(self):
        ''' Logs the user out of this session. '''
        SESSION.kill()
        raise web.seeother('/login')

    def POST(self):
        ''' Dummy, logs out the user from the current session. '''
        SESSION.kill()
        raise web.seeother('/login')


class Changepass:

    ''' A class that handles changing a users password. '''

    def __init__(self):
        self.chpform = form.Form(
                form.Password('oldpassword', form.notnull,
                            description='Old password'),
                form.Password('newpassword', form.notnull,
                            description='New password'),
                form.Password('newpassword2', form.notnull,
                            description='Confirm password'),
                form.Button('Confirm'),
                validators=[form.Validator("Passwords didn't match.",
                                lambda i: i.newpassword == i.newpassword2)])

    def GET(self):
        ''' Shows the change password page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            chpform = self.chpform()
            return RENDER.changepass(chpform)

    def POST(self):
        ''' Handles changing password. '''
        chpform = self.chpform()
        if not loggedin():
            raise web.seeother('/login')
        elif not chpform.validates():
            return RENDER.changepass(chpform)
        else:
            oldpassword = gethash(chpform['oldpassword'].value)
            newpassword = gethash(chpform['newpassword'].value)

        if oldpassword == newpassword:
            return RENDER.changepass(chpform)

        try:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            rows = dbh.select(USERTABLE, what='password',
                                where='user="{0}"'.format(SESSION.username))
            dbupass = rows[0].password
        except IndexError:
            SESSION.kill()
            raise web.internalerror()
        except OperationalError:
            raise web.internalerror()

        if dbupass == oldpassword:
            updatepassword(SESSION.username, newpassword)
            raise web.seeother('/')
        else:
            return RENDER.changepass(chpform)


#
# BEGIN
#

APP.notfound = notfound
application = APP.wsgifunc()

if __name__ == '__main__':
    APP.run()
