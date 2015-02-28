'''iTunes playlist music exporter.

Reads an iTunes-exported playlist (in XML) format and copies the files to a new location.

Then re-writes the playlist with the new location of each file.

Lorenzo Grespan at gmail.com'''
import argparse
import logging
import os
import shutil
import urllib

from lxml import etree

logging.getLogger().level = logging.INFO


def main():
    p = argparse.ArgumentParser()
    p.add_argument('xmlfile', help="The iTunes exported playlist")
    p.add_argument('itlib', help="Your iTunes playlist as a fullpath")
    p.add_argument('dstpath', help="Your destination path")
    args = p.parse_args()

    # add trailing slash
    dstpath_unix = os.path.join(args.dstpath, '')

    # encode for XML
    dstpath_enc = urllib.quote(dstpath_unix)
    itlib_enc = urllib.quote(args.itlib)

    if not os.path.exists(dstpath_unix):
        os.makedirs(dstpath_unix)

    r = etree.parse(args.xmlfile)

    # extract the 'music folder' tag and update it
    music_folder_xp = r.xpath('//key[.="Music Folder"]')[0].getnext()
    music_folder = music_folder_xp.text
    music_folder_fp = music_folder.replace(
        'file://{}'.format(itlib_enc), 'file://{}'.format(dstpath_enc)
    )
    music_folder_xp.text = music_folder_fp

    locations = r.xpath('//key[.="Location"]')
    for el in locations:
        # the location of each element in a URL-encoded format, with file:// prefix
        srcpath_enc_fullurl = el.getnext().text

        # destination path, to be saved in the XML element
        destpath_fullurl = srcpath_enc_fullurl.replace(
            'file://{}'.format(itlib_enc), 'file://{}'.format(dstpath_enc)
        )

        # decoded, with file:// prefix
        srcpath_dec_fullurl = urllib.unquote(srcpath_enc_fullurl)
        # decoded, as a UNIX path
        srcpath_dec_unix = srcpath_dec_fullurl.replace('file://', '')

        dst = srcpath_dec_unix.replace(args.itlib, dstpath_unix)

        if os.path.isfile(srcpath_dec_unix):
            dirs = os.path.dirname(dst)
            if not os.path.exists(dirs):
                os.makedirs(dirs)
            shutil.copy(srcpath_dec_unix, dirs)
            logging.debug('copied {} to {}'.format(srcpath_dec_unix, dirs))
        else:
            logging.error('NOT A PATH', srcpath_dec_unix)

        # save the new full path to the XML element
        el.getnext().text = destpath_fullurl

    dstxml_dir = os.path.dirname(args.xmlfile)
    dstxml_name = os.path.basename(args.xmlfile)
    new_xml = 'new_{}'.format(dstxml_name)
    dstxml_fullpath = os.path.join(dstxml_dir, new_xml)
    logging.debug('writing to {}'.format(dstxml_fullpath))
    r.write(dstxml_fullpath, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    logging.info('All done.\nNew playlist: {}.\nFiles are in {}'.format(
        dstxml_fullpath, dstpath_unix))

if __name__ == "__main__":
    main()
