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
import json, re, requests, subprocess

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

def get_text(t):
    if t:
        return clean_text(t.text)
    else:
        return ''

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

def main():
    img_url_template = 'https://valberedning.sverok.se/nominee_images/get_image/{}/400/400/true'
    nominees = []
    for id_ in all_ids(BeautifulSoup(requests.get('https://valberedning.sverok.se').content, 'html.parser')):
        url = 'https://valberedning.sverok.se/nominees/view/{}'.format(id_)
        nominee = {}

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

        info = soup.find('div', class_='info')
        nominee = {
                'name' : clean_text(info.h2.text),
                'info' : [(lbl.text, get_text(lbl.find_next_sibling('span'))) for lbl in info.find_all('label')],
                'nominations' : [tuple(clean_text(x.text) for x in li.find_all('span', limit=2)) for li in info.find('ul', class_='nominations').find_all('li')],
                'threeimportant' : [clean_text(t.find('label').text) for t in soup.find_all('div', class_='checkbox') if t.find('input').get('checked', False)],
                'whatiam' : [[clean_text(i.next_sibling.text) for i in t.find_all('input') if i.get('checked', False)] for t in soup.find_all('div', class_='input radio')],
                'questions' : []
        }

        nominee['questions'] = []
        for t in soup.find_all('div', class_='presentation'):
            qt = t.find('span', class_='question')
            if qt:
                ps = [clean_text(p.text) for p in t.find_all('p')]
                nominee['questions'].append((clean_text(qt.text), ps))

        img = soup.find('img').extract()
        m = re.match(r'^/nominee_images/get_image/(\d+)', img['src'])
        if m:
            r = requests.get(img_url_template.format(m.group(1)))
            fn = '{}.jpeg'.format(id_)
            open(fn, 'wb').write(r.content)
            nominee['imgsrc'] = fn
        else:
            nominee['imgsrc'] = 'useravatar.png'

        nominees.append(nominee)

    print(json.dumps(nominees))

if __name__ == '__main__':
    main()
