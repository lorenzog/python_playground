'''Short URL generator'''
from __future__ import print_function

import logging
import argparse
import string
import random
import sys
import threading
import time
import hashlib

CHARACTER_SET = ''.join([string.ascii_letters, string.digits])
SHORT_URL_LEN = 7

# Pool fine-tuning:
# if there are at least 10 short URLs in the pool, don't do anything
POOL_MIN_THRESHOLD = 10
# if there are less than 20 short URLs in the pool, start making more
POOL_MAKE_MORE_URLS = 20

# Data storage

# these could easily be REDIS instances (k/v stores)
hash_db = dict()
url_db = dict()

# if we're just generating random strings, need to lock on the URL db
# otherwise a race condition from another thread might cause
# duplicate URLs in the url db
url_db_lock = threading.RLock()

# if we're using a pool, we need no lock
# also, this could be a memcached instance somewhere
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
    # short_url = get_with_random_url(long_url)

    # second method: use a pool
    # short_url = get_with_url_pool(long_url)

    short_url = method(long_url)

    logging.debug('Received {}, generated {}'.format(long_url, short_url))
    print('.', sep='', end='')
    # artificially slow it down to see how the pool gets replenished
    time.sleep(random.random())


def get_with_random_url(long_url):
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


def get_with_url_pool(long_url):
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

        # ping the producer which will take care of
        # making new URLs if there aren't enough in the pool
        threading.Thread(target=producer).start()

        return s


def producer():
    '''Makes short, random URL strings and appends them
    to a shared pool'''
    if len(pool) > POOL_MIN_THRESHOLD:
        logging.debug("Plenty of fish")
        return

    # This guarantees at least MIN/2 pops before replenishm.
    while len(pool) < POOL_MAKE_MORE_URLS:
        logging.debug("Pool exhausting, making more")
        print('+', sep='', end='')
        s = _make_random_string()
        while s in url_db:
            s = _make_random_string()
        logging.debug("appending {} to pool".format(s))
        # no need to lock: if another producer makes
        # an identical random string, 
        pool.append(s)
    logging.debug("Pool replenished")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['pool', 'random'])
    parser.add_argument('total_runs', type=int)
    args = parser.parse_args()
    if args.method == 'pool':
        method = get_with_url_pool
    elif args.method == 'random':
        method = get_with_random_url
    else:
        sys.exit('Unsupported method')

    # initialise the pool
    producer()

    counter = 0
    while counter < args.total_runs:
        t0 = time.time()
        # spawns a new thread for each worker
        threading.Thread(
            target=worker_get,
            args=('a long url given to each worker with some'
                  'random content: {}'.format(
                      _make_random_string()
                  ),),
            kwargs={'method': method}
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
