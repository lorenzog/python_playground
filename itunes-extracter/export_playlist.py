'''iTunes playlist music exporter.

Reads an iTunes-exported playlist (in XML) format and copies the files to a new location.

Then re-writes the playlist with the new location of each file.

Needs editing:
    * replace the file:/// URL with the initial path of your iTunes music
    * the generated playlist does not seem to be itunes-compatible. 

Lorenzo Grespan at gmail.com'''
import argparse
import os
import urllib
import shutil

from lxml import etree


def main():
    p = argparse.ArgumentParser()
    p.add_argument('xmlfile')
    p.add_argument('itlib')
    p.add_argument('outpath')
    args = p.parse_args()

    # r = etree.parse('genre_ classic.xml')
    r = etree.parse(args.xmlfile)
    locations = r.xpath('//key[.="Location"]')
    for el in locations:
        # encoded path
        encpath = el.getnext().text
        cleanpath = urllib.unquote(encpath)

        encpath = encpath.replace('file:///Users/k/Music/Music', 'CLASSICAL')
        cleanpath = cleanpath.replace('file://', '')
        dst = cleanpath.replace('/Users/k/Music/Music', 'CLASSICAL')

        if not os.path.exists('CLASSICAL'):
            os.mkdir('CLASSICAL')

        if os.path.isfile(cleanpath):
            dirs = os.path.dirname(dst)
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            # print 'made dir', dirs
            shutil.copy(cleanpath, dirs)
            print 'copied {} to {}'.format(cleanpath, dirs)
        else:
            print 'NOT A PATH', cleanpath

        el.getnext().text = encpath
    r.write('out.xml', pretty_print=True)
    print 'now move out.xml and CLASSICAL together to the new location'

if __name__ == "__main__":
    main()
