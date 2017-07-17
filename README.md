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
2. Copy `config.txt.dist` to `config.txt` and customize the values as you like

### Icons

1. Install ImageMagick, optipng, and perl rename: `apt-get install imagemagick optipng perl`
2. Download and unzip the item icons from `http://webcdn.triongames.com/addons/assets/rift_item_icons.zip` and cd in to `item_icons`
3. Convert the icons to png, reduce their size, and lowercase the name because the icons are lowercased in `Items.xml`:

```
    for file in *.dds; do
       output=$(basename "$file" .dds).png;
       convert "$file" "$output"; 
       optipng -quiet "$output"; 
       prename 'y/A-Z/a-z/' "$output";
       rm "$file";
    done
```

## Running
Serve index.py via WSGI. The specifics and the (optional) HTTPd setup is beyond the scope of this README, but I am successfully using NGINX to proxy to [uwsgi](https://uwsgi-docs.readthedocs.io/en/latest/Python.html). A uwsgi config file is included (`appear.ini`).
                                                                                          
## Disclaimer

Trion, Trion Worlds, RIFT, Storm Legion, Nightmare Tide, Prophecy of Ahnket, Telara, and their respective logos, are trademarks or registered trademarks of Trion Worlds, Inc. in the U.S. and other countries. This project is not affiliated with Trion Worlds or any of its affiliates.

