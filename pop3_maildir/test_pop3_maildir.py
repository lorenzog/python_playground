import sqlite3
import tempfile

from mock import MagicMock, patch
from nose.tools import assert_raises

from pop3_maildir import setup_db, what_to_download, UidError, already_downloaded

# just set logging to debug
# import logging
# from pop3_maildir import log
# log.setLevel(logging.DEBUG)


class TestDb(object):
    def test_setup(self):
        tmpfile = tempfile.NamedTemporaryFile()
        print tmpfile.name
        conn = setup_db(tmpfile.name)
        conn.close()

        testconn = sqlite3.connect(tmpfile.name)
        testcur = testconn.cursor()
        testcur.execute('''SELECT * FROM fetched_msgs''')
        print testcur.fetchall()

        # no errors have been raised at this point

    def test_setup_nodb(self):
        pass

    def test_already_downloaded(self):
        '''Message already downloaded'''
        mock = MagicMock()
        cursor = mock.cursor.return_value
        # cursor.execute.return_value = [(u'date')]
        cursor.execute.fetchall.return_value = [(u'date')]
        ret = already_downloaded(mock, 1)
        assert ret is False


class TestPop(object):
    def test_one(self):
        '''Get one message'''
        pass

    def test_err(self):
        '''Error in retrieving message'''
        pass

    def test_del(self):
        '''Delete message'''
        pass

    def test_keep(self):
        '''Re-retrieve message'''
        pass


class TestWhatToDownload(object):
    def test_already_downl(self):
        '''DB returns all downloaded'''
        uidl = ['OK', ['1 a', '2 b', '3 c'], 42]
        mock = MagicMock()
        mock.return_value = True
        with patch('pop3_maildir.already_downloaded', mock):
            out = what_to_download(uidl, None)
        assert out == []

    def test_new_msgs(self):
        '''DB says all new'''
        uidl = ['OK', ['1 a', '2 b', '3 c'], 42]
        mock = MagicMock()
        mock.return_value = False
        with patch('pop3_maildir.already_downloaded', mock):
            out = what_to_download(uidl, None)
        assert out == [1, 2, 3]

    def test_errlist(self):
        '''F*ckd up list'''
        uidl = ['yadda yadda yadda']
        with assert_raises(UidError):
            what_to_download(uidl, None)

    def test_weird_uidls(self):
        '''msg number is not a number'''
        uidl = ['OK', ['a weird'], 42]
        with assert_raises(UidError):
            what_to_download(uidl, None)

    def test_weird_uidls2(self):
        '''msg number + uid has no space in between'''
        uidl = ['OK', ['1weird'], 42]
        with assert_raises(UidError):
            what_to_download(uidl, None)

    def test_weird_uidls3(self):
        '''A longer list (wrong)'''
        uidl = ['OK', ['1 weird', '1 msg', 'uid 3'], 42]
        mock = MagicMock()
        mock.return_value = False
        with patch('pop3_maildir.already_downloaded', mock):
            with assert_raises(UidError):
                what_to_download(uidl, None)

if __name__ == "__main__":
    t = TestDb()
    t.test_setup()
