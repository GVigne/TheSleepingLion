#!/bin/sh

# This script is meant to be run through MinGW


# Run pyinstaller
pyinstaller.exe the_sleeping_lion.py -D --collect-submodules=manimpango.utils --collect-submodules=thesleepinglion --collect-data=thesleepinglion --exclude-module=setuptools -w -y

# Set icon on exe
./ResourceHacker.exe -open ./dist/the_sleeping_lion/the_sleeping_lion.exe -save ./dist/the_sleeping_lion/the_sleeping_lion.exe -action delete -mask ICONGROUP
./ResourceHacker.exe -open ./dist/the_sleeping_lion/the_sleeping_lion.exe -save ./dist/the_sleeping_lion/the_sleeping_lion.exe -action addoverwrite -res the_sleeping_lion_square.ico -mask ICONGROUP,1,


# Zip
cd ./dist/the_sleeping_lion/
zip -r the_sleeping_lion.zip *
mv the_sleeping_lion.zip ../../
cd ../../

# Create windows installer
echo $(uname -m) > ARCH
pip show thesleepinglion | grep Version | cut -d $' ' -f 2 > VERSION
echo $(du -sk dist/the_sleeping_lion | cut -f 1) > INSTALLSIZE
makensis thesleepinglion.nsi

