'''Short URL generator'''
from __future__ import print_function

import logging
import string
import random
import sys
import threading
import time
import hashlib

CHARACTER_SET = ''.join([string.ascii_letters, string.digits])
SHORT_URL_LEN = 7
POOL_MIN_THRESHOLD = 10

TOTAL_RUNS = 1000

# these could easily be REDIS instances (k/v stores)
hash_db = dict()
url_db = dict()

# for method 1
url_db_lock = threading.RLock()

# for method 2
# this could be a memcached instance
pool = list()

# uncomment to see what's happening
# logging.getLogger().setLevel(logging.DEBUG)


def _make_random_string():
    '''Whatever you want to use to generate a random string'''
    return ''.join(
        random.choice(CHARACTER_SET) for i in range(SHORT_URL_LEN)
    )


def _hash(long_url):
    '''Generate a hash how you best see fit'''
    return hashlib.sha512(long_url).hexdigest()


def worker_get(long_url, method):
    '''Simulates a GET: user provides long URL, expects short one'''
    # first method: simply generate a random string and
    # in case of collision try again
    # short_url = _get_1(long_url)

    # second method: use a pool
    # short_url = _get_2(long_url)

    short_url = method(long_url)

    logging.debug('Received {}, generated {}'.format(long_url, short_url))
    print('.', sep='', end='')
    # artificially slow it down to see how the pool gets replenished
    time.sleep(random.random())


def _get_1(long_url):
    '''Generating a random URL every time.

    Pros: simpler.
    Cons: the more URLs are savd in url_db, the longer
        the query;
    Cons: the more URLs are saved, the more chances to hit a duplicate
    '''
    logging.debug("hash db: {}".format(repr(hash_db)))
    h = _hash(long_url)
    if h in hash_db:
        logging.debug("Url already in hash db")
        return hash_db.get(h)
    else:
        s = _make_random_string()
        print('.', sep='', end='')
        with url_db_lock:
            # ## this bit is an atomic op or locked on url_db
            while s in url_db:
                s = _make_random_string()
                print('*', sep='', end='')
            url_db[s] = long_url
            hash_db[h] = s
            # ## end atomic op
        return s


def _get_2(long_url):
    '''Using a short URL pool'''
    h = _hash(long_url)
    if h in hash_db:
        return hash_db.get(h)
    else:
        # emergency replenishing (blocking)
        if len(pool) == 0:
            producer()
        s = pool.pop()
        print('-', sep='', end='')
        url_db[s] = long_url
        hash_db[h] = s
        threading.Thread(target=producer).start()
        return s


def producer():
    if len(pool) > POOL_MIN_THRESHOLD:
        logging.debug("Plenty of fish")
        return

    # This guarantees at least MIN/2 pops before replenishm.
    while len(pool) < 2 * POOL_MIN_THRESHOLD:
        logging.debug("Pool exhausting, making more")
        print('+', sep='', end='')
        s = _make_random_string()
        while s in url_db:
            s = _make_random_string()
        logging.debug("appending {} to pool".format(s))
        pool.append(s)
    logging.debug("Pool replenished")


def main():
    # initialise the pool
    producer()
    counter = 0
    while counter < TOTAL_RUNS:
        t0 = time.time()
        threading.Thread(
            target=worker_get,
            args=('a long url given to thread with some'
                  'random content: {}'.format(
                      _make_random_string()
                  ),),
            kwargs={'method': _get_1}
        ).start()
        counter += 1
        sys.stdout.flush()
        t1 = time.time()

    total_time = t1 - t0
    urls_per_millisec = counter / total_time
    urls_per_sec = urls_per_millisec / 1000

    print('\n Throughput: {}'.format(urls_per_sec))

if __name__ == "__main__":
    main()
