#!/usr/bin/env python

"""Det här programmet hämtar alla kandidater från valberedning.sverok.se som har tackat ja till minst en nominering och lägger upp dem på Sveroks forum.

Den städar också HTMLen kraftigt, ty jag är perfektionist och koden som valberedning.sverok.se spottar ur sig är skräpig.

Det du behöver göra för att få det här programmet att fungera är att sätta rätt forumkod, rätt authkod och be forumgruppen om en api-nyckel.

Lycka till!
"""

from bs4 import BeautifulSoup
from itertools import chain
import re, requests

def call_me_maybe(f, v):
    if v:
        f(v)

def main():
    double_newline_pattern = re.compile(r'\n[\s^\n]*\n')
    soup = BeautifulSoup(requests.get('https://valberedning.sverok.se').content, 'html.parser')

    # Finn alla nominerade som inte tackat nej.
    for id_ in [e.get('data-id') for e in soup.find('div', class_='nominee-list').find_all('div', class_='nominee-list-item ')]:
        url = 'https://valberedning.sverok.se/nominees/view/{}'.format(id_)
        nominee = BeautifulSoup(requests.get(url).content, 'html.parser').find('div', class_='nominee-view')

        print(url)
        print('==========================================================================')

        base = soup.new_tag('div')
        call_me_maybe(base.append, nominee.find('div', class_='nominees view fieldset'))
        call_me_maybe(base.append, nominee.find('h3', class_='extra-margin'))
        call_me_maybe(base.append, nominee.find('form'))

        name = base.find('h2').string.strip()

        base.find('div', id='galleri').extract()

        for t in chain(base.find_all('br', style='clear:both;'), base.find_all(type='hidden'), base.find_all(style='display:none;'), base.find_all('hr'), base.find_all('img')):
            t.extract()

        for t in base.find_all(style=True):
            del t['style']

        for t in chain(base.find_all('div', class_='input radio'), base.find_all('div', class_='checkbox')):
            for l in t.find_all('label'):
                l.string = '\u00A0' + l.string.strip() # &nbsp;
                if t['class'] != ['checkbox']:
                    l.append(soup.new_tag('br'))
                l.unwrap()

        for t in base.find_all('label'):
            t.unwrap()

        colors = {'red' : '#F10000', 'green' : '#00D500'}
        for t in chain(base.find_all(class_='green'), base.find_all(class_='red')):
            c = colors[t['class'][0]]
            del t['class']
            t['style'] = 'color: {};'.format(c)

        for t in base.find_all('form'):
            t.unwrap()

        for t in base.find_all('span', class_='question'):
            if t.string is not None:
                h4 = soup.new_tag('h4')
                h4.string = t.string
                t.replace_with(h4)
            else:
                t.extract()

        for t in base.find_all('span', attrs=False):
            if not t.attrs:
                t.unwrap()

        for t in base.find_all('div', class_='presentation'):
            t.unwrap()

        for t in base.find_all('input'):
            del t['id']
            del t['value']
            del t['name']
            t['disabled'] = 'disabled'

        for t in base.find_all('div', class_='checkbox'):
            p = soup.new_tag('p')
            p.contents = t.contents
            t.replace_with(p)

        for t in chain(base.find_all('div', class_='input select'), base.find_all('div', class_='limit-wrapper'), base.select('div.info')):
            t.unwrap()

        for t in base.find_all('p'):
            if t.string is not None:
                ps = double_newline_pattern.split(t.string)
                if len(ps) > 1:
                    t.contents = ''
                    stuff = []
                    for p in ps:
                        p1 = soup.new_tag('p')
                        p1.string = p
                        stuff.append(p1)

                    t.replace_with(stuff[0])
                    for p2 in stuff[1:]:
                        stuff[0].insert_after(p2)

        base.find(class_='button send-message').extract()
        base.find(class_='nominees view fieldset').unwrap()

        link_to_nominator = soup.new_tag('a')
        link_to_nominator['href'] = url
        link_to_nominator.append('Länk till kandidatens sida på valberedning.sverok.se.')
        linkp = soup.new_tag('p')
        linkp.append(link_to_nominator)
        base.append(linkp)

        response = requests.post('http://forum.sverok.se/api/index.php?/forums/topics',
                                 auth=('MATA IN DIN AUTH-KOD HÄR.', ''),
                                 data={
                                     'forum' : 381,
                                     'author' : 904,
                                     'title' : name,
                                     'post' : ''.join(map(str, base.contents)).strip(),
                                     'hidden' : -1
                                 }
                                )

if __name__ == '__main__':
    main()
