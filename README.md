# vaktplan
Web applikasjon for å opprette og slette kommentarer i en kalender

For å kjøre koden i "debug" mode, sett attributten web.config.debug til sann.

    web.config.debug = True

Dersom du vil teste koden lokalt på maskin før det eventuelt legges på en webserver
med f.eks. wsgi så kan man eksekvere scriptet etter å ha gitt koden kjøre rettigheter.
En testserver vill bli opprettet som lytter på port 8080.

    chmod 755 vaktplan.py
    ./vaktplan.py

I koden så finner du en attributt som heter ALLOWED. Her legger du tupples med
brukernavn og passord, eksempel; 

    ALLOWED = (
      ('usertest', 'passwordtest'),
    )
