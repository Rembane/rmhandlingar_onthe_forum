#!/usr/bin/env python

"""Det här programmet hämtar alla kandidater från valberedning.sverok.se
som inte har tackat nej och konverterar den listan till en tex-fil.

Lycka till!
"""

from bs4 import BeautifulSoup
from functools import partial
from itertools import chain
import click, json, os.path, re, requests, subprocess, sys

@click.group()
def cli():
    pass

def validate_filetype(ctx, param, value, ts=None):
    suffix = os.path.splitext(value)[1]
    if suffix not in ts:
        raise click.BadParameter('Din filändelse var: {}, den stöds inte, använd en av följande istället: {}'.format(suffix, ', '.join(ts)))
    else:
        return (suffix, value)

input_filetypes = ('.json', '.tex', '.pdf')

output = click.argument('output', callback=partial(validate_filetype, ts=input_filetypes), type=click.Path())

@cli.command()
@click.argument('input', callback=partial(validate_filetype, ts=('.json', '.tex')), type=click.Path())
@output
def convert(input, output):
    """Konvertera filer till nya filformat.
    """
    if input_filetypes.index(input[0]) >= input_filetypes.index(output[0]):
        raise click.BadParameter('Du kan inte konvertera en {} till en {}. Försök med en annan kombination av filtyper.'.format(input[0], output[0]))

    def totex(data):
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

        result = [open('head.tex').read()]
        for n in data:
            result.extend([
                h1(n['name']),
                gfx(n['imgsrc']),
                table('{ll}', *n['info']),
                h2('Nomineringar'),
                table('{ll}', *n['nominations']),
                h2('Tre prioriterade'),
                ', '.join(n['threeimportant']),
                h2('Korta frågor, snabba svar'),
                ', '.join(x[0] for x in n['whatiam']),
                h2('Presentation')
            ])
            for q in n['questions']:
                result.append(h3(q[0]))
                result.extend([p for p in q[1]])
        result.append('\\end{document}')
        return '\n'.join(result)

    def dispatch(input, output):
        if input[0] == '.json':
            if output[0] == '.tex':
                with open(output[1], 'w') as o:
                    with open(input[1], 'r') as i:
                        o.write(totex(json.loads(i.read())))
            elif output[0] == '.pdf':
                # Konvertera först till tex
                o2 = ('.tex', os.path.splitext(output[1])[0] + '.tex')
                dispatch(input, o2)
                # Sen tex till pdf.
                dispatch(('.tex', o2[1]), output)
        elif input[0] == '.tex':
            subprocess.run(['latexmk', '-shell-escape', '-jobname={}'.format(os.path.splitext(output[1])[0]), '-pdf', input[1]])

    dispatch(input, output)

@cli.command()
@output
def scrape(output):
    """Hämta nominerade från valberedning.sverok.se.
    """

    def all_ids(soup):
        """Ge ett id i taget på nominerade som inte tackat nej.
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

    img_url_template = 'https://valberedning.sverok.se/nominee_images/get_image/{}/400/400/true'
    nominees = []
    for id_ in all_ids(BeautifulSoup(requests.get('https://valberedning.sverok.se').content, 'html.parser')):
        url = 'https://valberedning.sverok.se/nominees/view/{}'.format(id_)
        nominee = {}
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

    json_file = join(os.path.splitext(output[1])[0] + '.json')
    with open(json_file, 'w') as fh:
        fh.write(json.dumps(nominees))
        if output[0] != 'json':
            convert(('json', json_file), output)

if __name__ == '__main__':
    cli()
