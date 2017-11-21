#!/usr/bin/env python

"""Det här programmet hämtar alla kandidater från valberedning.sverok.se
som har tackat ja till minst en nominering och lägger upp dem på Sveroks forum.

Den städar också HTMLen kraftigt, ty jag är perfektionist och koden
som valberedning.sverok.se spottar ur sig är skräpig.

Det du behöver göra för att få det här programmet att fungera är att sätta rätt
forumkod, rätt authkod och be forumgruppen om en api-nyckel.

Lycka till!
"""

from bs4 import BeautifulSoup
from itertools import chain
import re, requests, subprocess

def call_me_maybe(f, v):
    if v:
        f(v)

def all_ids(soup):
    """Hämta alla idn på nominerade som inte tackat nej.
    """
    for e in soup\
            .find('div', class_='nominee-list')\
            .find_all('div', class_='nominee-list-item'):
        if 'turned-down' not in e['class']:
            yield e.get('data-id')

def clean_text(txt):
    return ' '.join(x.strip() for x in txt.splitlines())

def main2():
    soup = BeautifulSoup(requests.get('https://valberedning.sverok.se').content, 'html.parser')

    for id_ in all_ids(soup):
        url = 'https://valberedning.sverok.se/nominees/view/{}'.format(id_)
        soup = BeautifulSoup(requests.get(url).content, 'html.parser').find('div', class_='nominee-view')

        # Tidy städar HTML på ett fantastiskt vis.
        p = subprocess.run(['tidy', '-iq', '--hide-comments', 'yes',
            '--output-html', 'yes', '--bare', 'yes', '--clean', 'yes',
            '--hide-comments', 'yes', '--show-warnings', 'no',
            '--show-info', 'no', '--show-errors', '0'],\
                input=str(soup).encode('utf-8'),
                stdout=subprocess.PIPE,
                )

        # Ny soppa.
        soup = BeautifulSoup(p.stdout, 'html.parser')\
                .find('div', class_='nominee-view')

        # Gör info-tabellen till en riktig tabell.
        info = soup.find('div', class_='info')
        name = info.h2.text
        table1 = BeautifulSoup.new_tag(soup, name='table')
        for lbl in info.find_all('label'):
            row = BeautifulSoup.new_tag(soup, name='tr')
            c1  = BeautifulSoup.new_tag(soup, name='td')
            c2  = BeautifulSoup.new_tag(soup, name='td')
            c1.string = lbl.text
            s = lbl.find_next_sibling('span')
            if s:
                c2.string = clean_text(s.text)
            else:
                c2.string = ''
            row.append(c1)
            row.append(c2)
            table1.append(row)
        table2 = BeautifulSoup.new_tag(soup, name='table')
        for li in info.find('ul', class_='nominations').find_all('li'):
            [title, property] = [x.text for x in li.find_all('span', limit=2)]
            row = BeautifulSoup.new_tag(soup, name='tr')
            c1 = BeautifulSoup.new_tag(soup, name='td')
            c2 = BeautifulSoup.new_tag(soup, name='td')
            c1.string = title
            c2.string = property
            row.append(c1)
            row.append(c2)
            table2.append(row)
        info.clear()
        header = BeautifulSoup.new_tag(soup, name='h1')
        header.string = name
        h2 = BeautifulSoup.new_tag(soup, name='h2')
        h2.string = 'Nomineringar'
        for x in (header, table1, h2, table2):
            info.append(x)

        lw = soup.find('div', class_='limit-wrapper')
        if lw:
            table = BeautifulSoup.new_tag(soup, name='table')
            for t in soup.find_all('div', class_='checkbox'):
                row = BeautifulSoup.new_tag(soup, name='tr')
                c1  = BeautifulSoup.new_tag(soup, name='td')
                c2  = BeautifulSoup.new_tag(soup, name='td')
                c1.string = ''
                if t.find('input').get('checked', False):
                    c1.string = 'X'
                c2.string = clean_text(t.find('label').text)
                row.append(c1)
                row.append(c2)
                table.append(row)
            lw.replace_with(table)
        for t in soup.find_all('div', class_='input radio'):
            table = BeautifulSoup.new_tag(soup, name='table')
            for i in t.find_all('input'):
                row = BeautifulSoup.new_tag(soup, name='tr')
                c1  = BeautifulSoup.new_tag(soup, name='td')
                c2  = BeautifulSoup.new_tag(soup, name='td')
                c1.string = ''
                if i.get('checked', False):
                    c1.string = 'X'
                c2.string = clean_text(i.next_sibling.text)
                row.append(c1)
                row.append(c2)
                table.append(row)
            t.replace_with(table)

        # Uppa h3-taggarna en nivå
        for t in soup.find_all('h3'):
            t.name = 'h2'
            del t['class']

        # Byt ut span-question mot rubriker
        for t in soup.find_all('span', class_='question'):
            t.name = 'h3'
            del t['class']

        # Ta bort allt dumt
        for t in chain(soup.find_all('br', class_='c4'), soup.find_all('hr'), soup.find_all('a', class_='button'), soup.find_all('div', class_='c5'), soup.find_all('script'), soup.find_all('div', class_='addthis_toolbox')):
            t.extract()

        # Ta bort alla taggar som inte behöver wrappa andra taggar
        for t in chain(soup.find_all('form'), soup.find_all('div')):
            t.unwrap()

        img = soup.find('img').extract()
        img['src'] = ''.join(('https://valberedning.sverok.se', img['src']))
        soup.find('h1').insert_after(img)

        del soup['class']
        print(soup.prettify(formatter='html'))

if __name__ == '__main__':
    main2()
