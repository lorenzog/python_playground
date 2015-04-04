'''Short URL generator

This code is released under the GPL v3 license.'''
from __future__ import print_function

import logging
import argparse
import string
import random
import sys
import threading
import time
import hashlib

# what's in a short URL
CHARACTER_SET = ''.join([string.ascii_letters, string.digits])
# how long is it going to be
SHORT_URL_LEN = 7

# Pool fine-tuning: this guarantees that new URLs are added in batches
# if there are at least 10 short URLs in the pool, don't do anything
POOL_MIN_THRESHOLD = 10
# if there are less than 20 short URLs in the pool, start making more
POOL_MAKE_MORE_URLS = 20

# Data storage
# these could easily be REDIS instances (k/v stores)
hash_db = dict()
url_db = dict()

# if we're just generating random strings:
# then we must lock the URL db otherwise a race condition from another
# thread might cause duplicate URLs in the url db
url_db_lock = threading.RLock()

# if we're using a pool:
# also, this could be a memcached instance somewhere
pool = list()
# since the producer is a singleton, we use a locking mechanism
producer_lock = threading.RLock()

logging.basicConfig(format='%(message)s', level=logging.INFO)

# output to observe how urls are added and removed
behaviour = list()


def _make_random_string():
    '''Whatever you want to use to generate a random string'''
    return ''.join(
        random.choice(CHARACTER_SET) for i in range(SHORT_URL_LEN)
    )


def _hash(long_url):
    '''Generate a hash how you best see fit'''
    return hashlib.sha512(long_url).hexdigest()


# method 1
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
        behaviour.append('.')
        with url_db_lock:
            # ## this bit is an atomic op or locked on url_db
            while s in url_db:
                s = _make_random_string()
                behaviour.append('*')
            url_db[s] = long_url
            hash_db[h] = s
            # ## end atomic op
        return s


# method 2
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
        behaviour.append('-')
        url_db[s] = long_url
        hash_db[h] = s

        # ping the producer which will take care of
        # making new URLs if there aren't enough in the pool
        threading.Thread(target=producer).start()

        return s


def producer():
    '''Makes short, random URL strings and appends them
    to a shared pool'''

    # using a lock to simulate a singleton
    with producer_lock:
        if len(pool) > POOL_MIN_THRESHOLD:
            logging.debug("Plenty of fish")
            return

        # This guarantees at least MIN/2 pops before replenish.
        while len(pool) < POOL_MAKE_MORE_URLS:
            logging.debug("Pool exhausting, making more")
            behaviour.append('+')
            s = _make_random_string()
            while s in url_db or s in pool:
                # found dup; try again
                s = _make_random_string()
            logging.debug("appending {} to pool".format(s))
            pool.append(s)
        logging.debug("Pool replenished")


def worker_get(long_url, method):
    '''Simulates a GET: user provides long URL, expects short one'''
    # using the provided method
    short_url = method(long_url)
    logging.debug('Received {}, generated {}'.format(long_url, short_url))
    behaviour.append('.')
    # artificially slow it down to see how the pool gets replenished
    # time.sleep(random.random())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['pool', 'random'])
    parser.add_argument('total_runs', type=int)
    args = parser.parse_args()
    if args.method == 'pool':
        method = get_with_url_pool
        explanation = ("Dots are requests of short URLs\n"
                       "'+' means new URL added to pool;\n"
                       "'-' means short URL popped from pool")
    elif args.method == 'random':
        method = get_with_random_url
        explanation = ("Dots are generations of random short URL;\n"
                       "'*' means a conflict was found and a string "
                       "had to be re-generated")
    else:
        sys.exit('Unsupported method')

    # initialise the pool
    producer()

    counter = 0
    t0 = time.time()
    while counter < args.total_runs:
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
    urls_per_sec = counter / total_time

    print(''.join(behaviour))
    print('\n Done {} requests in {} sec.\nThroughput: {} requests/sec'.format(counter, total_time, urls_per_sec))
    print(explanation)

if __name__ == "__main__":
    main()
