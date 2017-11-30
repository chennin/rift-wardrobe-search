#!/usr/bin/env python3.5
#Copyright 2017 Christopher Henning

#Permission is hereby granted, free of charge, to any person obtaining a copy of
#this software and associated documentation files (the "Software"), to deal in
#the Software without restriction, including without limitation the rights to
#use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#of the Software, and to permit persons to whom the Software is furnished to do
#so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re
import os
import sys
from lxml import etree
import pymysql.cursors
from pymysql.err import (Error, OperationalError)
from pathlib import Path
from six.moves import configparser
import csv

# Read config file in
mydir = os.path.dirname(os.path.realpath(__file__))
configReader = configparser.RawConfigParser()
configFile = Path(mydir + "/config.ini")
if configFile.is_file():
  configReader.read(mydir + "/config.ini")
else:
  print("Error: config file {0} not found.".format(configFile.as_posix()), file=sys.stderr)
  sys.exit(1)

config = {}
try:
  for var in ["SQLUSER", "SQLLOC", "SQLPASS", "SQLDB"]:
    config[var] = configReader.get("Appearances",var)
except configparser.NoOptionError:
  print("Error: required configuration option {0} not found.".format(var), file=sys.stderr)
  sys.exit(2)

namekeys = {
   'kind': "Item",               'firsttag': "FirstLootedBy",    'nametag': "Name",        'idtag': "ItemKey",
}

try:
  conn = pymysql.connect(host=config['SQLLOC'], user=config['SQLUSER'], password=config['SQLPASS'], db=config['SQLDB'], charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
except pymysql.err.OperationalError as e:
  print("Error connecting to database: {0}".format(e), file=sys.stderr)
  sys.exit(3)

# Insert Items from Items.xml
with conn.cursor() as cursor:
  # Iterative parser so we don't run out of memory
  context = etree.iterparse("{0}s.xml".format(namekeys['kind']), events=('end',))
  toadd = []
  # Do nothing if item already exists
  sql = "INSERT INTO items (`ItemKey`, `AddonType`, `Icon`, `Slot`, `Type`, `Name/English`) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE ItemKey=VALUES(ItemKey), `Name/English`=VALUES(`Name/English`)";

  for event, elem in context:
    # <Item>, <Quest>, etc
    if elem.tag == namekeys['kind']:
      # ID number for this
      iid = elem.find(namekeys['idtag']).text

      # Friendly (English) name for this
      what = ""
      whatelem = elem.find(namekeys['nametag']).find("English")
      if whatelem is not None:
        what = whatelem.text
      if what == "":
        what = "-MISSING-NAME-"

      addontype = elem.find('AddonType').text
      icon = elem.find('Icon').text
      # Only care about wardrobe pieces
      slot = ""
      if elem.find('Slot') is not None and elem.find('Slot').text in ['Cape', 'Chest', 'Feet', 'Gloves', 'Helmet', 'Legs', 'MainHand', 'OffHand', 'OneHand', 'Shoulders', 'TwoHanded', 'Weapon_2h', 'Weapon_Main', 'Weapon_Off', 'Weapon_Ranged']:
        slot = elem.find('Slot').text
      else:
        continue

      thetype = elem.find('WeaponType')
      if thetype is None:
        thetype = elem.find('ArmorType')
      if elem.find('Consumable') is not None or thetype is None or thetype.text in ["1h_flower", "2h_flower", "2h_shovel"]:
        equiptype = "Costume"
      else:
        equiptype = thetype.text

      toadd.append( (iid, addontype, icon, slot, equiptype, what) )
      # Insert thousands of rows at once for massive speedup
      if len(toadd) > 2000:
        cursor.executemany(sql, toadd)
        toadd = []
        conn.commit()

      # Free the just-parsed XML nodes to keep memory usage low
      elem.clear()
      while elem.getprevious() is not None:
        del elem.getparent()[0]

  # Execute any last parsed nodes
  if len(toadd) > 0:
    cursor.executemany(sql, toadd)
  conn.commit()

# Insert appearances - TSV file
with conn.cursor() as cursor:
  toadd = []
  with open("rift-wardrobe-appearances-for-items-from-discoveries-2017-10-31.txt") as tsv:
    sql = "UPDATE items SET `Appearance`=%s WHERE `ItemKey`=%s";
    for line in csv.reader(tsv, dialect="excel-tab"):
      key = line[1]
      appearance = line[5]
      toadd.append( (appearance, key) )
      if len(toadd) > 2000:
        cursor.executemany(sql, toadd)
        toadd = []
        conn.commit()
  # Commit last ones
  if len(toadd) > 0:
    cursor.executemany(sql, toadd)
  conn.commit()
  conn.close()
