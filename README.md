# vaktplan

Web application to create and delete comments in a calendar.

To run the code in "debug" mode, set the attribute web.config.debug to true.

    web.config.debug = True

If you wish to test the code locally on your machine before putting it on a
webserver with for example wsgi you can execute the script after giving it
execution rights and removing the comment for the last two lines in the code.
A test server will be created that listens on port 8080.

    chmod 755 vaktplan.py
    ./vaktplan.py

In the code you will find an attribute called ALLOWED. Put tuples in it
containing the username and password. Example;

    ALLOWED = (
      ('usertest', 'passwordtest'),
    )

There is a situation/bug with webpy's session handler. For some reason I don't
understand the session folder needs 777 rights. If you do not create the
folder, the script will create it, but it will not be able to use the created
folder unless you chmod 777 it.
