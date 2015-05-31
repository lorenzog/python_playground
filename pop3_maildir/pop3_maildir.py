'''Prototype POP3 to Maildir fetcher.

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

# TODO import configs
# TODO sqlite for digests

MAILDIR = 'HERE_GOES_LOCAL_MAILDIR'
POP3_SERVER = 'POP3_server'
USER = 'user'


log = logging.getLogger(__name__)


def getpass():
    pass


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
        return ''


def connect_and_logon():
    m = poplib.POP3_SSL(POP3_SERVER)
    m.user(USER)
    m.pass_(getpass())
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
                log.debug("Dry run: not adding to inbox, not deleting from server")
                log.info(msg)
                log.info('\n')
                continue
            log.debug("Got it, now adding to inbox")
            inbox.add('\n'.join(msg))
            log.debug("Deleting message from server")
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
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true')
    args = parser.parse_args()
    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug('Debug messages enabled')

    inbox = mailbox.Maildir(MAILDIR, msgfactory)

    m = connect_and_logon()

    # m.list()
    # log.debug('There are {} messages'.format(len(m.list())))
    (num_msgs, total_size) = m.stat()
    log.debug("There are {} messages, for a total of {} octets".format(
        num_msgs, total_size))

    get_messages(m, inbox, num_msgs, args.dry_run)


if __name__ == "__main__":
    main()
