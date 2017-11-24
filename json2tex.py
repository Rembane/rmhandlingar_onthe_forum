#!/usr/bin/env python

import json, sys

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

def main():
    print(open('head.tex').read())
    for n in json.loads(sys.stdin.read()):
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

if __name__ == '__main__':
    main()
