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
    if isinstance(txt, str):
        return ' '.join(x.strip() for x in str(txt).splitlines())
    else:
        return txt

def new_table_row(soup, *args):
    row = BeautifulSoup.new_tag(soup, name='tr')
    for a in args:
        c = BeautifulSoup.new_tag(soup, name='td')
        if isinstance(a, str):
            c.string = clean_text(a)
        else:
            c.append(a)
        row.append(c)
    return row

def main2():
    img_url_template = 'https://valberedning.sverok.se/nominee_images/get_image/{}/400/400/true'
    for id_ in all_ids(BeautifulSoup(requests.get('https://valberedning.sverok.se').content, 'html.parser')):
        url = 'https://valberedning.sverok.se/nominees/view/{}'.format(id_)

        # Tidy städar HTML på ett fantastiskt vis.
        # Ös in vår nominee view i Tidy och gör roliga grejer med det som kommer ut.
        p = subprocess.run(['tidy', '-iq', '--hide-comments', 'yes',
            '--output-html', 'yes', '--bare', 'yes', '--clean', 'yes',
            '--hide-comments', 'yes', '--show-warnings', 'no',
            '--show-info', 'no', '--show-errors', '0'],\
                input=str(BeautifulSoup(requests.get(url).content, 'html.parser').find('div', class_='nominee-view')).encode('utf-8'),
                stdout=subprocess.PIPE,
                )

        soup = BeautifulSoup(p.stdout, 'html.parser')\
                .find('div', class_='nominee-view')

        # Gör info-tabellen till en riktig tabell.
        info = soup.find('div', class_='info')
        name = info.h2.text
        table1 = BeautifulSoup.new_tag(soup, name='table')
        for lbl in info.find_all('label'):
            s = lbl.find_next_sibling('span')
            table1.append(new_table_row(soup, lbl.text, s if s else ''))
        table2 = BeautifulSoup.new_tag(soup, name='table')
        for li in info.find('ul', class_='nominations').find_all('li'):
            [title, property] = [x.text for x in li.find_all('span', limit=2)]
            table2.append(new_table_row(soup, title, property))
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
                table.append(new_table_row(soup, 'X' if t.find('input').get('checked', False) else '', t.find('label').text))
            lw.replace_with(table)
        for t in soup.find_all('div', class_='input radio'):
            table = BeautifulSoup.new_tag(soup, name='table')
            for i in t.find_all('input'):
                table.append(new_table_row(soup, 'X' if i.get('checked', False) else '', i.next_sibling.text))
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

        # Ta bort alla class-attribut.
        for t in soup.find_all():
            del t['class']

        img = soup.find('img').extract()
        m = re.match(r'^/nominee_images/get_image/(\d+)', img['src'])
        if m:
            img['src'] = img_url_template.format(m.group(1))
        else:
            img['src'] = 'https://valberedning.sverok.se/img/useravatar.png'
        soup.find('h1').insert_after(img)

        del soup['class']
        print(soup.prettify(formatter='html'))

if __name__ == '__main__':
    main2()
