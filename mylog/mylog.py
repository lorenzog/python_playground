#!/usr/bin/env python
import argparse
import datetime
# import imp
import logging
import os
import subprocess
import tempfile


haz_tkinter = False
try:
    # imp.find_module('tkSimpleDialog')
    # haz_tkinter = True
    import Tkinter
    root = Tkinter.Tk(className="My own time logger")
    root.withdraw()
    import tkSimpleDialog
    haz_tkinter = True
except ImportError:
    pass

LOGFILE = os.path.expanduser('~/mylog.txt')

today = datetime.datetime.today()


def _log(message):
    logging.info(message)
    print "Message appended to {}".format(LOGFILE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--message')
    args = parser.parse_args()

    logging.basicConfig(filename=LOGFILE, format='%(asctime)s - %(message)s', level=logging.INFO, datefmt="%Y/%m/%d %a %H:%M")

    if args.message:
        _log(args.message)
    elif haz_tkinter:
        # try asking via GUI
        msg = tkSimpleDialog.askstring("Activity log", "What have you done lately?")
	if msg:
            _log(msg)
    else:
        tmpfile = tempfile.NamedTemporaryFile()
        editor = os.getenv('EDITOR')
        if not editor:
            editor = 'vi'
        subprocess.check_call([editor, tmpfile.name])
        with open(tmpfile.name) as f:
            f.seek(0, os.SEEK_END)
            _curpos = f.tell()
            if _curpos == 0:
                print "No message provided, aborting"
                return
            f.seek(0)
            msg = f.read().replace('\n', '--')

        # if today.weekday() == 0:
        #     # newline for week break
        #     _log('\n')
        _log(msg)


if __name__ == "__main__":
    main()
    exit(0)
