#!/usr/bin/env python
# coding: latin1


'''
Vaktplan is a calendar meant to be used by me privately. I have
uploaded it to Github and released it under the BSD license simply
because maybe, someone would like to use it them selves or use it as a
starter point to learn python/web.py

Vaktplan support basic loggin in/logging out. The passwords are never
stored in clear but as sha256 hex digest in a database. It is possible
to change password after logging in.

Syntax to create the database needed to run the application.

sqlite> CREATE TABLE vaktplan (
    comment TEXT,
    date TEXT,
    cdate DATE,
    user INTEGER,
    FOREIGN KEY(user) REFERENCES users(rowid)
);
sqlite> CREATE TRIGGER insert_date_created AFTER INSERT ON vaktplan
    ...> BEGIN
    ...> UPDATE vaktplan SET cdate = datetime('now')
    ...> WHERE rowid = new.rowid;
    ...> END;
sqlite>
sqlite> CREATE TABLE users (user TEXT, password TEXT, cdate DATE);
sqlite> CREATE TRIGGER insert_date_user_created AFTER INSERT ON users
    ...> BEGIN
    ...> UPDATE users SET cdate = datetime('now')
    ...> WHERE rowid = new.rowid;
    ...> END;
sqlite>
'''


import calendar
import datetime
import hashlib
import web

from sqlite3 import OperationalError


#
# Settings / Config
#


DEBUG = False
AUTORELOAD = False

DBTYPE = 'sqlite'
DBFILENAME = '/srv/www/kalender.moshwire.com/production/vaktplan.db'
DBTABLE = 'vaktplan'
USERTABLE = 'users'
TEMPLATEFOLDER = '/srv/www/kalender.moshwire.com/production/templates/'
SESSIONSFOLDER = '/srv/www/kalender.moshwire.com/production/sessions/'


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


def seeother(self):
    ''' Function intended to be hooked into classes where GET and/or
    POST functions are not needed. The function will forward the user
    to / or /login depending on if the user is logged in or not. '''
    if loggedin():
        raise web.seeother('/')
    else:
        raise web.seeother('/login')


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
        self.POST = seeother

    def __str__(self):
        return repr("Index: {0}.{1}".format(self.month, self.year))

    def GET(self):
        ''' Returns the index page. '''
        if loggedin():
            return RENDER.index(MONTHS, self.year, self.month)
        else:
            raise web.seeother('/login')


class Ym:

    ''' Shows the "month" page. '''

    def __init__(self):
        i = web.input()
        cal = calendar.Calendar(0)
        self.POST = seeother

        try:
            self.year = int(i.year)
            self.month = int(i.month)
        except:
            raise web.internalerror()
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


class Day:

    ''' Shows the "day" page. '''

    def __init__(self):
        i = web.input()
        self.POST = seeother

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

            rows = dbh.select(DBTABLE, what='comment,rowid,user',
                                            where='date="{0}.{1}.{2}"'.format(
                                            self.day, self.month, self.year))
            comments = []
            for row in rows:
                tmpstore = row
                comments.append([tmpstore.comment, tmpstore.rowid,
                                                                tmpstore.user])
            rows = dbh.select(USERTABLE, what='rowid,user')
            users = {}
            for row in rows:
                tmpstore = row
                users[tmpstore.rowid] = tmpstore.user

            return RENDER.day(MONTHS, DAYS, self.year, self.month, self.day,
                    self.weekday, comments, users)


class Add:

    ''' Adds data from page to database. '''

    def __init__(self):
        i = web.input()
        self.GET = seeother

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
                        user=SESSION.userid,
                        date="{0}.{1}.{2}".format(self.day, self.month,
                                                                self.year))
            except:
                trans.rollback()
                raise
            else:
                trans.commit()
                raise web.seeother('/ym/d/?year={0}&month={1}&day={2}'.format(
                                            self.year, self.month, self.day))


class Del:

    ''' Deletes data from page to database. '''

    def __init__(self):
        i = web.input()
        self.GET = seeother

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
        self.login = web.form.Form(
                web.form.Textbox('username', web.form.notnull,
                                                    description='Username'),
                web.form.Password('password', web.form.notnull,
                                                    description='Password'),
                web.form.Button('Login', class_="btn btn-blue"))

    def GET(self):
        ''' Shows the login page. '''
        login = self.login()
        return RENDER.login(login, None)

    def POST(self):
        ''' Process the login credentials. '''
        login = self.login()

        if not login.validates():
            return RENDER.login(login, None)
        else:
            username = login['username'].value
            hpassword = gethash(login['password'].value)

        try:
            dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
            rows = dbh.select(USERTABLE, what='password,rowid',
                                        where='user="{0}"'.format(username))
            tmpstore = rows[0]
            dbupass = tmpstore.password
            userid = tmpstore.rowid
        except IndexError:
            return RENDER.login(login, 'Username or password is wrong'.upper())
        except OperationalError:
            raise web.internalerror()

        if(hpassword == dbupass):
            SESSION.loggedin = True
            SESSION.username = username
            SESSION.userid = userid
            raise web.seeother('/')
        else:
            return RENDER.login(login, 'Username or password is wrong'.upper())


class Logout:

    ''' Class that handles logging users out of the system. '''

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
        self.chpform = web.form.Form(
                web.form.Password('oldpassword', web.form.notnull,
                                                description='Old password'),
                web.form.Password('newpassword', web.form.notnull,
                                                description='New password'),
                web.form.Password('newpassword2', web.form.notnull,
                                            description='Confirm password'),
                web.form.Button('Confirm', class_="btn btn-blue"),
                validators=[web.form.Validator("Passwords didn't match.",
                                lambda i: i.newpassword == i.newpassword2)])

    def GET(self):
        ''' Shows the change password page. '''
        if not loggedin():
            raise web.seeother('/login')
        else:
            chpform = self.chpform()
            return RENDER.changepass(chpform, None)

    def POST(self):
        ''' Handles changing password. '''
        chpform = self.chpform()
        if not loggedin():
            raise web.seeother('/login')
        elif not chpform.validates():
            return RENDER.changepass(chpform, None)
        else:
            oldpassword = gethash(chpform['oldpassword'].value)
            newpassword = gethash(chpform['newpassword'].value)

        if oldpassword == newpassword:
            return RENDER.changepass(chpform, 'The new password can not be the same as the new one'.upper())

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
            return RENDER.changepass(chpform, 'Password entered wrong'.upper())


#
# BEGIN
#


APP.notfound = notfound
application = APP.wsgifunc()

if __name__ == '__main__':
    APP.run()
