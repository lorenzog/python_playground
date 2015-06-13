'''POP3 to Maildir fetcher.

THIS IS WORK IN PROGRESS. Seriously, use at own risk.

The idea is to invoke gpg to read the password from an encrypted file
like offlineimap does. Fetchmail seems overly complicated to configure
(and I am not even sure it can do it!) and I don't want to store my
password in cleartext.

Code freely inspired by examples on the python website.

This code is under the GNU GPLv3 License.

Author: Lorenzo Grespan <lorenzo.grespan@gmail.com>
'''
import argparse
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

# TODO import configs

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


DRY_RUN = False
DEFAULT_DB = os.path.expanduser('~/.pop3_maildir.sqlite')


class UserNotFoundError(Exception):
    pass


class UidError(Exception):
    pass


def already_downloaded(db_conn, uid):
    c = db_conn.cursor()
    c.execute('''SELECT date FROM fetched_msgs WHERE uid = ?''', (uid,))
    ret = c.fetchall()
    print ret
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
    log.debug('Inserting into db: {} {}'.format(date, uid))
    c.execute('''INSERT INTO fetched_msgs VALUES (?, ?)''',
              (date, uid))
    db_conn.commit()


# uidl = unique id list
def what_to_download(uidl, db_conn):
    '''Decides which messages to download and returns a list of their id'''
    to_download = list()
    # ['response', ['mesgnum uid', ...], octets]
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

        for msgno in msg_to_download:
            log.debug("Processing message {}".format(msgno))
            # log.debug("Message {} not downloaded yet. Retrieving...".format(msgno))
            (header, msg, octets) = pop3_server.retr(msgno)

            if DRY_RUN:
                log.info(":: DRY RUN ::")
                log.info('\n'.join(msg))
                log.info(":: DRY RUN ::")
                log.info('\n')
                continue

            log.debug("Got it, now adding to inbox")
            inbox.add('\n'.join(msg))
            # do we really need this?
            inbox.flush()
            mark_retrieved(db_conn, msgno)
            log.debug("Kept record in db")

            if not keep:
                log.debug("Deleting message from server")
                pop3_server.dele(msgno)
                log.debug("Message deleted from server")

            log.info("Successfully retrieved message {} of {}".format(msgno, num_msgs))
    except poplib.error_proto as e:
        log.error("Didn't work out sorry: {}".format(e))
    except mailbox.error as e:
        log.error("Mailbox error: {}".format(e))

    pop3_server.quit()
    log.info("All messages retrieved and stored")

    if not keep:
        log.info("Messages not deleted from server")


def _get_gpg_pass(account, storage):
    '''Reads GPG-encrypted file, returns second item after 'account' or None.

    Format of the file:
        account password
    '''
    command = ("gpg", "-d", storage)
    # get attention
    print '\a'  # BEL
    # TODO catch exceptions
    output = subprocess.check_output(command)
    for line in output.split('\n'):
        r = re.match(r'{} ([a-zA-Z0-9]+)'.format(account), line)
        if r:
            return r.group(1)
    return None


def getpass(username, pwfile):
    '''Generic wrapper for obtaining the password.'''
    # TODO add code to read OSX keychain, etc.
    password = _get_gpg_pass(username, pwfile)

    log.debug("User: {}, pwfile: {}, password: {}".format(
        username, pwfile, password))
    if not password:
        raise UserNotFoundError
    return password


def connect_and_logon(server, username, password):
    '''Connects to the POP3 server and returns a 'server' object.

    Any error would be raised as poplib.error_proto, which is OK.
    '''
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
    parser.add_argument('server')
    parser.add_argument('username')
    parser.add_argument('pwfile', help="Password file")
    parser.add_argument('maildir')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true', default=False)
    parser.add_argument('-k', '--keep', action='store_true', default=False,
                        help="Do not delete messages on server")
    parser.add_argument('--db-location', default=DEFAULT_DB)
    parser.add_argument('-a', '--fetch_all', action='store_true', default=False)
    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug('Debug messages enabled')
    log.info('Fetching mail for user {} on server {}'.format(
        args.username, args.server))

    if args.dry_run:
        global DRY_RUN
        DRY_RUN = True

    # setup db
    db_conn = setup_db(args.db_location)
    # setup inbo
    inbox = setup_inbox(args.maildir)
    # setup server connection
    password = getpass(args.username, args.pwfile)
    pop3_server = connect_and_logon(args.server, args.username, password)
    # no longer needed
    del password

    # TODO when errors are raised, do something nice.
    get_messages(pop3_server,
                 inbox,
                 db_conn,
                 keep=args.keep,
                 fetch_all=args.fetch_all)

    db_conn.close()


if __name__ == "__main__":
    main()
