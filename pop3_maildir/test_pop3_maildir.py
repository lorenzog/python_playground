import sqlite3
import tempfile

from pop3_maildir import setup_db


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




if __name__ == "__main__":
    t = TestDb()
    t.test_setup()
