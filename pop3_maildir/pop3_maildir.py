'''POP3 to Maildir fetcher.

Usage: see README.md.

Code freely inspired by examples on the python website.

Copyright: 2015, Lorenzo Grespan <lorenzo.grespan@gmail.com>

This code is under the GNU GPLv3 License. See file gpl.txt.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import argparse
import ConfigParser
import datetime
import email
import email.Errors
import logging
import mailbox
import os
import poplib
import re
import subprocess
import sqlite3
import sys

# TODO import configs

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


DRY_RUN = False
DEFAULT_DB = os.path.expanduser('~/.pop3_maildir.sqlite')
DEFAULT_CONFIG_FILE = os.path.expanduser('~/.pop3_maildir.cfg')


class UserNotFoundError(Exception):
    pass


class UidError(Exception):
    pass


def already_downloaded(db_conn, uid):
    c = db_conn.cursor()
    c.execute('''SELECT date FROM fetched_msgs WHERE uid = ?''', (uid,))
    ret = c.fetchall()
    # ret: [(u'date'), (u'date2'), ...]
    # more than one means it's an old message
    if len(ret) > 0:
        # just print the whole output
        log.debug('Message with id {} already retrieved on {}'.format(
            uid, ret))
        return True
    return False


def mark_retrieved(db_conn, uid):
    # use pop3_server.uidl() to get digest, compare with mailbox, see if already present?
    # or keep list of downloaded messages somewhere else
    # open conn
    date = datetime.datetime.now().isoformat()
    c = db_conn.cursor()
    log.debug('Inserting into db:fetched_msgs: {} {}'.format(date, uid))
    if not DRY_RUN:
        c.execute('''INSERT INTO fetched_msgs VALUES (?, ?)''',
                  (date, uid))
        db_conn.commit()


# uidl = unique id list
def what_to_download(uidl, db_conn):
    '''Decides which messages to download and returns a list of their id'''
    to_download = list()
    # ['response', ['mesgnum uid', ...], octets]
    log.debug('Querying server for UIDLs returned: {}'.format(uidl))
    try:
        (_resp, uidl_msgs, _octets) = uidl
    except ValueError as e:
        raise UidError("UIDL not in expected format: {}".format(e))

    for uid_str in uidl_msgs:
        # ['msgnum uid']
        _uid = uid_str.split(' ', 1)
        # _uid is ['msgnum', 'uid']
        if len(_uid) != 2:
            raise UidError('UIDL list does not match expected format')
        msgno, uid = _uid
        try:
            msgno = int(msgno)
        except ValueError as e:
            raise UidError('Message number not a number: ({}) {}'.format(e, msgno))

        if already_downloaded(db_conn, uid):
            log.debug("Message {} already downloaded. Skipping".format(msgno))
            continue
        else:
            log.debug("Message {} is new. Adding to download list".format(msgno))
            to_download.append(msgno)

    return to_download


def get_messages(pop3_server, inbox, db_conn, keep=False, fetch_all=False):
    '''Core method: fetches messages from POP3 server and stores them in mailbox'''
    # pop3_server.list()
    # log.debug('There are {} messages'.format(len(pop3_server.list())))
    (num_msgs, total_size) = pop3_server.stat()
    log.debug("There are {} messages, for a total of {} octets".format(
        num_msgs, total_size))

    try:
        # determine which messages have been downloaded already
        if not fetch_all:
            uidls = pop3_server.uidl()
            msg_to_download = what_to_download(uidls, db_conn)
        else:
            msg_to_download = list(range(1, num_msgs + 1))
        log.debug('Messages to download: {}'.format(msg_to_download))

        for msgno in msg_to_download:
            log.debug("Processing message {}".format(msgno))
            # log.debug("Message {} not downloaded yet. Retrieving...".format(msgno))
            (header, msg, octets) = pop3_server.retr(msgno)

            if DRY_RUN:
                log.info(":: DRY RUN ::")
                log.info('\n'.join(msg))
                log.info(":: DRY RUN ::")
                log.info('\n')
                # continue

            log.debug("Got it, now adding to inbox")
            if not DRY_RUN:
                inbox.add('\n'.join(msg))
                # do we really need this?
                inbox.flush()
            mark_retrieved(db_conn, msgno)
            log.debug("Kept record in db")

            if keep:
                log.info('Keeping message {} on server')
            else:
                log.debug("Deleting message from server")
                if not DRY_RUN:
                    pop3_server.dele(msgno)
                log.debug("Message deleted from server")

            log.info("Successfully retrieved message {} of {}".format(msgno, num_msgs))
    except poplib.error_proto as e:
        log.error("Didn't work out sorry: {}".format(e))
    except mailbox.error as e:
        log.error("Mailbox error: {}".format(e))

    pop3_server.quit()
    log.info("\n :: All messages retrieved and stored")

    if keep:
        log.info(" :: Messages not deleted from server")


def _get_gpg_pass(account, storage):
    '''Reads GPG-encrypted file, returns second item after 'account' or None.

    Format of the file:
        account password
    '''
    command = ("gpg", "-d", storage)
    # get attention
    print '\a'  # BEL
    # TODO catch exceptions nicely?
    output = subprocess.check_output(command)
    for line in output.split('\n'):
        r = re.match(r'{} ([a-zA-Z0-9]+)'.format(account), line)
        if r:
            return r.group(1)
    return None


def getpass(username, pwfile):
    '''Generic wrapper for obtaining the password.'''
    log.debug("User: {}, pwfile: {}".format(username, pwfile))

    # TODO pgrep for keyboard-sharing program like synergyc, kill -STOP them
    # use os.kill(synergy_pid, signal.SIGSTOP
    # TODO add code to read OSX keychain based on platform (os.name..)
    password = _get_gpg_pass(username, pwfile)
    # then kill -CONT to unfreeze them

    if not password:
        raise UserNotFoundError
    return password


def connect_and_logon(server, username, password):
    '''Connects to the POP3 server and returns a 'server' object.

    Any error would be raised as poplib.error_proto, which is OK.
    '''
    log.debug('Connecting to {} with username: {}'.format(server, username))
    # imagine the fun if this was susceptible to MitM attacks.
    pop3_server = poplib.POP3_SSL(server)
    pop3_server.user(username)
    pop3_server.pass_(password)
    return pop3_server


def msgfactory(fp):
    '''Using email rather than the deprecated, default rfc822 module'''
    try:
        return email.message_from_file(fp)
    except email.Errors.MessageParseError as e:
        log.error('Error in parsing message: {}'.format(e))
        # Don't return None since that will
        # stop the mailbox iterator
        # TODO really? Check this - might be worth to return an error so the
        # message doesn't get deleted from the POP3 server.
        return ''


def setup_inbox(maildir):
    inbox = mailbox.Maildir(maildir)
    # TODO try with msgfactory
    # inbox = mailbox.Maildir(maildir, msgfactory)
    return inbox


def setup_db(db_location):
    '''Sets up the sqlite storage'''
    log.debug('Setting up db at {}'.format(db_location))
    if not os.path.exists(db_location):
        log.info('Creating database as it does not exist: {}'.format(db_location))
    conn = sqlite3.connect(db_location)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fetched_msgs (date TEXT, uid TEXT)''')
    conn.commit()

    return conn


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('server')
    # parser.add_argument('username')
    # parser.add_argument('pwfile', help="Password file")
    # parser.add_argument('maildir')
    parser.add_argument('-a', '--account', help="Only fetch mail for the specified account")
    parser.add_argument('-c', '--config',
                        help="Configuration file. Default {}".format(
                            DEFAULT_CONFIG_FILE),
                        default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true', default=False)
    parser.add_argument('-k', '--keep', action='store_true', default=False,
                        help="Do not delete messages on server")
    parser.add_argument('--db-location', default=DEFAULT_DB)
    parser.add_argument('-f', '--fetch_all', action='store_true', default=False)
    parser.add_argument('--really-show-password', help="Show password in debug log",
                        action='store_true', default=False)
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug('Debug messages enabled')

    cfg = ConfigParser.SafeConfigParser()

    if not os.path.exists(args.config):
        log.error("Config file not found: {}".format(args.config))
        sys.exit(3)
    with open(args.config) as cf:
        cfg.readfp(cf)

    accounts = cfg.sections()
    # if user supplied one account to fetch mail for,
    if args.account:
        if args.account in accounts:
            accounts = args.account
        else:
            log.error("Specified account '{}' not in config file {}".format(
                args.account, args.config))
            sys.exit(1)

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True

    # setup db
    db_conn = setup_db(args.db_location)

    for account in accounts:
        try:
            username = cfg.get(account, 'username')
            server = cfg.get(account, 'server')
            pwfile = os.path.expanduser(
                cfg.get(account, 'pwfile'))
            maildir = os.path.expanduser(
                cfg.get(account, 'maildir'))
        except ConfigParser.NoOptionError as e:
            log.error("Missing mandatory option for account {} "
                      "in config file: {}".format(account, e))
            sys.exit(2)

        log.info('\n :: Fetching mail for user {} on server {}'.format(
            username, server))
        # setup inbox
        inbox = setup_inbox(maildir)
        # setup server connection
        password = getpass(username, pwfile)
        if args.really_show_password:
            log.debug('Password: {}'.format(password))
        else:
            log.debug('*Not showing password in debug log*')

        pop3_server = connect_and_logon(server, username, password)
        # no longer needed
        del password

        # TODO when errors are raised, do something nice?
        get_messages(pop3_server,
                     inbox,
                     db_conn,
                     keep=args.keep,
                     fetch_all=args.fetch_all)

    # any exceptions from above would stop the program and close the db_conn
    db_conn.close()


if __name__ == "__main__":
    main()
