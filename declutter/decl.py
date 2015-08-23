'''uwsgi --http :9090 --wsgi-file foobar.py'''
import argparse
from HTMLParser import HTMLParser
import logging
import subprocess
import tempfile

import requests

# to use aaron's cleaner
import sys
sys.path.append('html2text')
import html2text


log = logging.getLogger('decl')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

# command line for html2text
HTML2TEXT = ['html2text', '-ascii']
# HTML2TEXT = ['html2text', '-style', 'pretty']


# my own implementation
class MyParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        log.debug("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        log.debug("Encountered an end tag :", tag)

    def handle_data(self, data):
        log.debug("Encountered some data  :", data)

parser = MyParser()


def myparser_cleanup(localfile):
    with open(localfile) as f:
        stuff = f.read()

    out = parser.feed(stuff)
    return out


def beautifulsoup_cleanup(localfile):
    log.debug("Using beautiful soup 4")
    with open(localfile) as f:
        html_doc = f.read()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')
    # http://stackoverflow.com/a/5598678/204634
    for s in soup('script'):
        print s.extract()
    return soup.get_text()


def html2text_cleanup(localfile):
    log.info("Using html2text")
    cmdline = list(HTML2TEXT)
    cmdline.append(localfile)
    # alternative, reading file directly
    # (found on SO, forgot to note the link :( )
    # from subprocess import Popen, PIPE, STDOUT
    # p = Popen(['myapp'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    # stdout_data = p.communicate(input='data_to_write')[0]
    out = subprocess.check_output(cmdline)
    return out


def usage():
    log.info("Usage")


# Thanks Aaron, also for this.
# https://github.com/aaronsw/html2text
def aaron_cleanup(tmpfile):
    log.info("Using aaron's cleanup")
    h = html2text.HTML2Text()
    # h.ignore_links = True
    import codecs
    with codecs.open(tmpfile, encoding='utf-8') as f:
        content = f.read()

    # content_decoded = unicode(content, errors='replace')
    # out = h.handle(content_decoded)
    out = h.handle(content)
    # log.debug(
    #     h.handle("<p>Hello, <a href='http://earth.google.com/'>world</a>!")
    # )
    return out


def read_from_url(url):
    '''Dumps the content of the URL into a temporary file then cleans it up'''
    log.debug("reading from {}".format(url))
    # XXX why is not deleted?
    tmpfile = tempfile.NamedTemporaryFile()
    try:
        with open(tmpfile.name, 'wb') as f:
            response = requests.get(url)
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        log.error(e)
        return e.message
    # now read from file
    log.debug("saved into {}".format(tmpfile.name))
    return cleanup(tmpfile.name)


def read_from_file(where):
    return html2text_cleanup(where)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--localfile')
    parser.add_argument('-u', '--url')
    parser.add_argument('-d', '--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    done_something = False

    out = list()
    if args.localfile:
        _out = read_from_file(args.localfile)
        out.append(_out)
        done_something = True

    if args.url:
        _out = read_from_url(args.url)
        out.append(_out)
        done_something = True

    if not done_something:
        usage()
    else:
        log.info('\n'.join(out))


# cleanup = html2text_cleanup
# cleanup = myparser_cleanup
# cleanup = aaron_cleanup
cleanup = beautifulsoup_cleanup

if __name__ == '__main__':
    main()
