#/usr/bin/env python3.5
#Copyright (c) 2017 Christopher S Henning
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
from six.moves import configparser
from yattag import Doc
import os
import pymysql.cursors
import sys
import re, string
from urllib.parse import parse_qsl

UPDATED = "2017-09-05"

# Read config file in
mydir = os.path.dirname(os.path.realpath(__file__))
configReader = configparser.RawConfigParser()
success = configReader.read(mydir + "/config.ini")
if not success:
   sys.exit("Missing configuration file {0}/config.ini".format(mydir))

config = {}
configitems =  ["SQLUSER", "SQLDB", "SQLLOC", "SQLPASS" ]
for var in configitems:
  try:
    config[var] = configReader.get("Appearances",var)
  except configparser.NoSectionError:
    sys.exit("Missing configuration section 'Appearances'")
  except (configparser.NoOptionError):
    sys.exit("Missing configuration item {0}. {1} are required.".format(var, ", ".join(configitems)))

# Limit query results for when someone searches for "a"
maxresults = 300

# WSGI function
def application(environ, start_response):
    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    env = dict(parse_qsl(request_body.decode()))
    # Initialize search parameters
    search = { 'appearance': "", }
    for var in search:
       if var in env:
          search[var] = env[var]

    # Filter invalid input
    pattern = re.compile('\W+')
    pattern.sub('', search['appearance'])

    results = None
    # The model is to print verbose errors to console/log, and print a generic error to Web page
    # Initialize generic error here
    error = None
    # search the DB for input
    if search['appearance'] != "":
      query = "SELECT * FROM items WHERE `Appearance` LIKE %s"
      query += " ORDER BY `Appearance`, `Name/English` LIMIT {}".format(maxresults)

      connection = None
      try:
         connection = pymysql.connect(host=config["SQLLOC"],
                             user=config["SQLUSER"],
                             password=config["SQLPASS"],
                             db=config["SQLDB"],
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
      except Exception as e:
         # This just kills one WSGI worker which will be respawned
         # Maybe find how to kill the WSGI server if we assume connection problems (eg wrong pass) are fatal
         print("Failed to connect to SQL database. {0}".format(e), file=sys.stderr)
         error = "Something went wrong with the SQL connection."

      if connection:
         try:
            with connection.cursor() as cursor:
               cursor.execute(query, "%" + search['appearance'] + "%")
               results = cursor.fetchall()
         except Exception as e:
            print(e, file=sys.stderr)
            error = "Something went wrong with the SQL query."
         finally:
            connection.close()

    # OK, now start constructing HTML
    doc, tag, text, line = Doc(defaults = {'appearance': search['appearance']}).ttl()
    doc.asis('<!DOCTYPE html>')
    with tag('html'):
       with tag('head'):
          doc.stag('meta', ('http-equiv', "Content-Type"), ('content', "text/html; charset=utf-8"))
          doc.stag('link', ('rel', "stylesheet"), ('type', "text/css"), ('href', "style.css"))
          doc.stag('link', ('rel', "stylesheet"), ('type', "text/css"), ('href', "https://www.magelocdn.com/pack/magelo-bar-css2.css"))
          # Script tags cannot be self-closing, thus this construct with the 'pass'
          with tag('script', ('src', "https://www.magelocdn.com/pack/rift/en/magelo-bar.js#1"), ('type', "text/javascript")):
             pass
          with tag('title'):
             text("RIFT Wardrobe Appearance Search")
       with tag('body'):
          # Prevent Cloudflare interpreting Player@Shard as email
          doc.asis("<!--email_off-->")
          # Intro / search boxes
          with tag('h2'):
             text("RIFT Wardrobe Appearance Search")
          line('p', "Which items in RIFT give a particular cosmetic appearance? Search below to find the ones you are missing.")
          with tag('p'):
             text("Data is combination of items from Trion's ")
             line('a', "public assets", href = "http://webcdn.triongames.com/addons/assets/")
             text(" and information generously released by ")
             line('a', "Emilynicole@Deepwood", href = "http://forums.riftgame.com/technical-discussions/addons-macros-ui/496667-wardrobe-appearances-list-completed.html#post5313180")
             text(".")
          with tag('p'):
             line('em', UPDATED)
          with tag('form', ('id', "appform")):
             line('label', "Appearance name: ", ('for', "appearance"))
             doc.stag('input', ('type', "text"), ('name', "appearance"), ('id', "appearance"), ('size', "24"), ('maxlength', "255"), ('value', search['appearance'] if search['appearance'] != "" else ""))
             doc.stag('input', ('type', "submit"), ('formmethod', "post"))
          with tag('p'):
            text("Enter a ")
            line('strong', "wardrobe appearance to search for")
            text(" - in English - then press ")
            line('strong', "Submit")
            text(". You can see the ones you are missing by going to the Wardrobe tab of your character sheet in-game and checking the Show Uncollected box.")
          # If we had an earlier error, print the generic message here
          if error:
             line('p', error)
          # Print search results
          lastapp = ""
          if results is not None:
            idx = 0
            reslen = len(results)
            with tag('h3'):
              text("Results for ")
              with tag('em'):
                text("*{0}*".format(search['appearance']))
              text(":")
            if reslen >= maxresults:
              with tag('p'):
                text("WARNING: results capped at {} and may be incomplete. Use a more specific search term.".format(maxresults))
            elif reslen <= 0:
              line('p', "None!")
            # Manually go through the loop so we can properly separate different appearances
            # and list duplicates in shorthand
            while idx < reslen:
              if results[idx]['Appearance'] != lastapp:
                with tag('p', klass='container'):
                  doc.stag('img', src="{}.png".format(results[idx]['Icon']))
                  with tag('strong'):
                    text(" {}".format(results[idx]['Appearance']))
                  text(" is given by:")
                lastapp = results[idx]['Appearance']
                # An appearance
                with tag('ul'):
                  while idx < reslen and results[idx]['Appearance'] == lastapp:
                    # An item that gives the apperance
                    with tag('li'):
                      line('a', results[idx]['Name/English'], href = "https://rift.magelo.com/en/item/{}".format(results[idx]['ItemKey']))
                      if results[idx]['Type'] == "Costume":
                        line('div', " (Costume Item)", title = "Costume Item", klass = "costume")
                      lastname = results[idx]['Name/English']
                      count = 1
                      idx += 1
                      # Print other items of the same name that give the appearance on the same line
                      # Strip trailing whitespace because some possibly-suffixed items come with a trailing space
                      while idx < reslen and lastname.rstrip() == results[idx]['Name/English'].rstrip():
                        text(", ")
                        count += 1
                        line('a', "{0:02d}".format(count), href = "https://rift.magelo.com/en/item/{}".format(results[idx]['ItemKey']))
                        if results[idx]['Type'] == "Costume":
                          line('div'," (C)",title = "Costume Item", klass = "costume")
                        idx += 1
                      text(".")
          with tag('p'):
            text('See other RIFT tools ')
            line('a', "here", href="https://rift.events/main.html")
            text('.')
              
    start_response('200 OK', [('Content-Type','text/html')])
    return [doc.getvalue().encode('utf8')]
