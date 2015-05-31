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
import email
import email.Errors
import logging
import mailbox
import poplib
import re
import subprocess

# TODO import configs
# TODO sqlite for digests

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


def get_gpg_pass(account, storage):
    '''Reads GPG-encrypted file, returns second item after username.

    Example:

        user pass
    '''
    command = ("gpg", "-d", storage)
    # get attention
    print '\a'  # BEL
    output = subprocess.check_output(command)
    for line in output.split('\n'):
        r = re.match(r'{} ([a-zA-Z0-9]+)'.format(account), line)
        if r:
            return r.group(1)
    return None


def getpass(username, pwfile):
    # TODO add code to read OSX keychain, etc.
    return get_gpg_pass(username, pwfile)


# UIDL format:
#  ['1 1430130312.M437107P2470V000000000000FE10I0000000051906D54_0.jacques,S=2770',
# ['response', ['mesgnum uid', ...], octets]
def already_downloaded(uidl):
    # use m.uidl() to get digest, compare with mailbox, see if already present?
    # or keep list of downloaded messages somewhere else
    # TODO: for now let's skip this
    return False


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


def connect_and_logon(server, username, pwfile):
    m = poplib.POP3_SSL(server)
    m.user(username)
    password = getpass(username, pwfile)
    log.debug("User: {}, pwfile: {}, password: {}".format(
        username, pwfile, password))
    # TODO if not password: raise error
    m.pass_(password)
    return m


def get_messages(m, inbox, num_msgs, dry_run=True):
    try:
        for i in range(1, num_msgs + 1):
            log.debug("Processing message {} of {}".format(i, num_msgs))
            _uidl = m.uidl(i)
            if already_downloaded(_uidl):
                log.debug("Message {} already downloaded. Skipping".format(i))
                continue
            log.debug("Message {} not downloaded yet. Retrieving...".format(i))
            (header, msg, octets) = m.retr(i)

            if dry_run:
                log.debug(":: DRY RUN ::")
                log.info('\n'.join(msg))
                log.debug(":: DRY RUN ::")
                log.info('\n')
                continue

            log.debug("Got it, now adding to inbox")
            # TODO wanna check for errors like, out of memory?
            inbox.add('\n'.join(msg))
            log.debug("Deleting message from server")
            # XXX IMPORTANT
            m.dele(i)

            log.debug("Message deleted from server")

            # do we really need this?
            inbox.flush()
            log.info("Successfully retrieved message {} of {}".format(i, num_msgs))
    except poplib.error_proto as e:
        log.error("Didn't work out sorry: {}".format(e))
    except mailbox.error as e:
        log.error("Mailbox error: {}".format(e))
    m.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('server')
    parser.add_argument('username')
    parser.add_argument('pwfile', help="Password file")
    parser.add_argument('maildir')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug('Debug messages enabled')
    else:
        log.info('Not verbose')

    inbox = mailbox.Maildir(args.maildir)
    # TODO try with msgfactory
    # inbox = mailbox.Maildir(args.maildir, msgfactory)

    # TODO check for errors
    m = connect_and_logon(args.server, args.username, args.pwfile)

    # m.list()
    # log.debug('There are {} messages'.format(len(m.list())))
    (num_msgs, total_size) = m.stat()
    log.debug("There are {} messages, for a total of {} octets".format(
        num_msgs, total_size))

    # TODO when errors are raised, do something nice.
    get_messages(m, inbox, num_msgs, args.dry_run)


if __name__ == "__main__":
    main()
