# Vaktplan

Add support for sending emails using the local SMTP daemon.
Add functionality so that vakplan tells you who has committed a comment
    and at which time the person did so.
Add functionality so that one can chose if a comment is to be deleted
    from the database or just marked as deleted.
Add functionality so that an administrator can add new users.
Add a setup script or functionality in the script that will check for
    required tables in the database and create them if they are not
    there and the user tells the script to create them.

All sections containing forms need to be reviewed. The error messages
    are difficult to understand or just looks terrible.

Write a proper README file. It should contain information about the
    database, wsgi and apache setup. Maybe even a minimal setup
    description. Write about how to set up the whole thing without
    exposing the python script itself.
