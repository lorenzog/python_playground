POP3 e-mail to Maildir
======================

A minimal python e-mail fetcher for POP3 servers with support for Maildir and gpg-encrypted password files.

Usage:

    python pop3_maildir.py

The above command assumes you have a configuration file in `$HOME/.pop3_maildir.cfg` like this one:

    > [foo]
    > server=mail.example.com
    > username=user@example.com
    > pwfile=mypwfile.gpg
    > maildir=~/Mail/Mailboxes/example.com/inbox

Where:

 * `pwfile` is a GPG-encrypted file of the format <username> <password>
 * `maildir` is a local maildir

For other options, see:

    python pop3_maildir.py -h

This tool supports  *only* POP3 SSL servers.

What is a maildir
-----------------

A maildir is a UNIX directory that contains three sub-directories:

    the_maildir/
        cur/
        new/
        tmp/

For more information and a good reason why Maildir is much better than your local spool file, see http://cr.yp.to/proto/maildir.html


Why GPG-encrypted files
-----------------------

Because I never liked leaving my passwords in cleartext on my filesystem.


Why another tool
----------------

Because although I used to use `fetchmail` it took me longer to understand its options and whether I could use an encrypted file to store my password than writing my own tool in Python. Perhaps `fetchmail` has gotten a bit bloated or is simply poorly documented (or rather, too documented and requires hours of reading for even the simplest operation).
