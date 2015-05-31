'''Prototype POP3 to Maildir fetcher.

The idea is to invoke gpg to read the password from an encrypted file
like offlineimap does. Fetchmail seems overly complicated to configure
(and I am not even sure it can do it!) and I don't want to store my
password in cleartext.

Code freely inspired by examples on the python website.
'''
import mailbox
import poplib

inbox = mailbox.Maildir('HERE_GOES_LOCAL_MAILDIR')

m = poplib.POP3_SSL('POP3_SERVER')
m.user('USERNAME')
m.pass_('...guess')
m.list()
(numMsgs, totalSize) = m.stat()
for i in range(1, numMsgs + 1):
    # use m.uidl() to get digest, compare with mailbox, see if already present?
    # or keep list of downloaded messages somewhere else
    (header, msg, octets) = m.retr(i)
    inbox.add('\n'.join(msg))
m.quit()
inbox.flush()
