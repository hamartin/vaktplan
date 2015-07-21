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
'''

import base64
import calendar
import datetime
import re
import web


#
# Settings / Config
#

DEBUG = False
AUTORELOAD = False

DBTYPE = 'sqlite'
DBFILENAME = 'vaktplan.db'
DBTABLE = 'vaktplan'
TEMPLATEFOLDER = 'templates/'


#
# Statics
#


URLS = (
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
web.config.debug = DEBUG
APP = web.application(URLS, globals(), autoreload=AUTORELOAD)
RENDER = web.template.render(TEMPLATEFOLDER, base='layout')


#
# Functions
#


def notfound():
    ''' Returns custom 404 page. '''
    return web.notfound(RENDER.notfound())


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
        return RENDER.index(MONTHS, self.year, self.month)


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
        return RENDER.ym(MONTHS, self.year, self.month, self.dateslist,
                self.dayin, self.monthin)


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
        dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
        rows = dbh.select(DBTABLE, what='comment,rowid',
                where='date="{0}.{1}.{2}"'.format(
                    self.day, self.month, self.year))

        return RENDER.day(MONTHS, DAYS, self.year, self.month, self.day,
                self.weekday, rows)


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
        ''' Only here to make sure no one tries to fool the site. '''
        raise web.notfound()

    def POST(self):
        ''' Stores data to the database and sends the user back to the
        same page. '''
        dbh = web.database(dbn=DBTYPE, db=DBFILENAME)
        trans = dbh.transaction()
        try:
            dbh.insert(DBTABLE, comment=self.comment,
                    date="{0}.{1}.{2}".format(self.day, self.month,
                        self.year))
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
        ''' Only here to make sure no one tries to fool the site. '''
        raise web.notfound()

    def POST(self):
        ''' Deletes data from the database and sends the user back to
        the same page. '''
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


#
# BEGIN
#

APP.notfound = notfound
application = APP.wsgifunc()

#if __name__ == '__main__':
    #APP.run()
