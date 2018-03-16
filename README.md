# RIFT Wardrobe Cosmetic Search 

Find out which items in RIFT give a particular cosmetic appearance.

Uses Items.xml from the [Trion public assets](http://webcdn.triongames.com/addons/assets/) and data collected by [a player](http://forums.riftgame.com/technical-discussions/addons-macros-ui/496667-wardrobe-appearances-list-completed.html#post5313180).

## Requirements

* Python 3.5
* Yattag: `pip install yattag` , or on Ubuntu 16.10+, `apt-get install python-yattag`
* A WSGI such as uwsgi 

Tested on Ubuntu 16.04.

## Example

http://rift.events/appearances/

## Install

1. Clone the source code via git
2. Copy `config.ini.dist` to `config.ini` and customize the values as you like

### Icons

1. Install ImageMagick and optipng: `apt-get install imagemagick optipng`
2. Download and unzip the item icons from `http://webcdn.triongames.com/addons/assets/rift_item_icons.zip` and cd in to `item_icons`. This folder should end up at the same level as `index.py`.
3. Convert the icons to png, reduce their size, and lowercase the name because the icons are lowercased in `Items.xml`:

```
    ls *.dds | while read file; do
       output=$(echo $(basename "$file" .dds).png | tr "[:upper:]" "[:lower:]");
       [ -f "$output" ] && continue;
       convert "$file" "$output"; 
       optipng -quiet "$output"; 
    done;
    rm -f *.dds;
```

### Inserting Data

1. Get Items.xml from the latest `Rift_Discoveries_*.zip` from the Trion public assets folder, and the mapping of items to appearances from the above forum thread (named `rift-wardrobe-appearances-for-items-from-discoveries-2017-7-20.txt` or similar) and place them in the same folder as parse.py.
2. Create a MySQL database and user.
3. Create a table:

```
CREATE TABLE `items` (
  `ItemKey` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `AddonType` varchar(96) COLLATE utf8_unicode_ci DEFAULT NULL,
  `Icon` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `Slot` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `Type` varchar(16) COLLATE utf8_unicode_ci DEFAULT NULL,
  `Name/English` varchar(96) COLLATE utf8_unicode_ci DEFAULT NULL,
  `Appearance` varchar(96) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ItemKey`),
  KEY `name` (`Name/English`),
  KEY `app` (`Appearance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
```

4. Run `python3 ./parse.py` .


## Running
Serve index.py via WSGI. The specifics and the (optional) HTTPd setup is beyond the scope of this README, but I am successfully using NGINX to proxy to [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/Python.html). A uwsgi config file is included (`appear.ini`).
                                                                                          
## Disclaimer

Trion, Trion Worlds, RIFT, Storm Legion, Nightmare Tide, Prophecy of Ahnket, Telara, and their respective logos, are trademarks or registered trademarks of Trion Worlds, Inc. in the U.S. and other countries. This project is not affiliated with Trion Worlds or any of its affiliates.

