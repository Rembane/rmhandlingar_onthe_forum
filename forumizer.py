#!/usr/bin/env python3

"""Hej! :D

main hämtar alla filer du ger som argument till programmet och lägger dem i Verksamhetsplan- och budget-forumet, medan main2 hämtar alla filer som du ger som argument till programmet och lägger dem i Inkomna motioner-forumet.

Det går att skriva programmet mycket snyggare, men det lämnas som en övning till läsaren. Jag tar med glädje emot pull requests. :)

Lycka till!
"""

import requests, subprocess, os.path, sys

PANDOC_PATH = '/home/hace/.local/bin/pandoc'

def main(filenames):
    for fn in filenames:
        print(fn)
        result = subprocess.run([PANDOC_PATH, '--to=html', fn], stdout=subprocess.PIPE)
        result.check_returncode()

        response = requests.post('http://forum.sverok.se/api/index.php?/forums/topics',
                                 auth=('MATA IN DIN AUTH-KOD HÄR.', ''),
                                 data={
                                     'forum' : 379,
                                     'author' : 904,
                                     'title' : os.path.basename(os.path.splitext(fn)[0]),
                                     'post' : result.stdout,
                                     'hidden' : -1
                                 }
                                )
        print(response)

def main3(filenames):
    for fn in filenames:
        print(fn)
        result = subprocess.run([PANDOC_PATH, '--to=html', fn], stdout=subprocess.PIPE)
        result.check_returncode()

        response = requests.post('http://forum.sverok.se/api/index.php?/forums/topics',
                                 auth=('MATA IN DIN AUTH-KOD HÄR.', ''),
                                 data={
                                     'forum' : 378,
                                     'author' : 904,
                                     'title' : os.path.basename(os.path.splitext(fn)[0]),
                                     'post' : result.stdout,
                                     'hidden' : -1
                                 }
                                )
        print(response)

if __name__ == '__main__':
    main3(sys.argv[1:])
    # main(sys.argv[1:])
    # main2()

