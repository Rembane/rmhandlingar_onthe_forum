#!/usr/bin/env python

"""Det här programmet hämtar alla kandidater från valberedning.sverok.se
som inte har tackat nej och konverterar den listan till en tex-fil.

Lycka till!
"""

from bs4 import BeautifulSoup
from itertools import chain
import json, re, requests, subprocess, sys

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

def scrape():
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

    return nominees

def totex():
    def table(spec, *rows):
        return '\n'.join([
            '\\begin{tabular}' + spec,
            ' \\\\\n'.join(' & '.join(row) for row in rows),
            '\\end{tabular}'])

    def gfx(path):
        return '\\begin{figure}[H]\n\\centering\n\\includegraphics[width=\\textwidth]{%s}\n\\end{figure}' % (path,)

    def h1(s):
        return '\\newpage\\section{%s}\n' % (s,)
    def h2(s):
        return '\\subsection{%s}\n' % (s,)
    def h3(s):
        return '\\subsubsection{%s}\n' % (s,)

    print(open('head.tex').read())
    for n in data:
        print(h1(n['name']))
        print(gfx(n['imgsrc']))
        print(table('{ll}', *n['info']))
        print(h2('Nomineringar'))
        print(table('{ll}', *n['nominations']))
        print(h2('Tre prioriterade'))
        print(', '.join(n['threeimportant']))
        print(h2('Korta frågor, snabba svar'))
        print(', '.join(x[0] for x in n['whatiam']))
        print(h2('Presentation'))
        for q in n['questions']:
            print(h3(q[0]))
            for p in q[1]:
                print(p)
    print('\\end{document}')

def topdf(s):
    fn = 'alla_nominerade.tex'
    with open(fn, 'w') as fh:
        fh.write(s)
    subprocess.run(['latexmk', '-shell-escape', '-pdf', fn])

# In: Ja/Nej?
# Ut: json, tex, pdf

def main():
    try:
        a = sys.argv[1]
    except IndexError:
        pass
    else:
        if a == 'scrape':
            print(json.dumps(scrape()))
            sys.exit(0)
        elif a == 'totex':
            print(totex(json.loads(sys.stdin.read())))
            sys.exit(0)
        elif a == 'topdf':
            topdf(totex(json.loads(sys.stdin.read())))
            sys.exit(0)
    print('Välj scrape eller totex eller topdf.')


if __name__ == '__main__':
    main()
