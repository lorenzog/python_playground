Url shortener
=============

This proof-of-concept code uses two distinct methods to generate short
URLs with performance in mind:

 * The first method generates a random string and checks its uniqueness
 * The second method uses a producer/consumer pattern with a pool of
   unique URLs

Usage:

    $ python shortn.py random 10000
    $ python shortn.py pool 10000

Where the last parameter is the number of "requests".

Sample output: in the 'random' version every dot is a new random URL,
and every * is a "collision":

    [snip]
    ....................................................................................................

    Done 10000 requests in 75.8780860901 sec.
    Throughput: 131.790356285 requests/sec

In the 'pool' version every dot is a request for a short URL, every plus
sign is the producer creating new short URLs and every minus is a pop()
from the pool:

    [snip]
    .-.--.-.++++++++++-.-.-..-.-.--.-.-..--..+++++++++++-.-.--..-.-.-.--..-++++++++++.---...--.

    Done 10000 requests in 5.06192183495 sec.
    Throughput: 1975.53425874 requests/sec

Technical details
-----------------

In both instances a worker receives a long URL to shorten. It calculates
its hash so that it can return the same short URL for the same
original URL. If the hash is new then it is a new URL. The worker then
"gets" a new short URL and returns it to the calling function.

Depending on the method used the worker either generates a random string
or picks one from a pool. The main difference is that the first method
must check the uniqueness of the string every time with a lock on the
shared "short URL" dataase; the second uses a "producer" thread that
replenishes the pool when it is depleting. The producer takes care of
checking the uniquenes and this does not slow down the worker.

The code uses Python's data structures but in a fairly agnostic way.
There are no "tricks" in the core algorithm which shoud be replicable in
any modern programming language that supports threading and basic
locking mechanisms.

Porting to real life
--------------------

The "hash DB" and "short URL DB" can be mapped to key/value stores (e.g.
REDIS) while the "short URL pool" could be a memcached instance shared
between workers.

Pros and cons
-------------

Method 1: random strings.

Pros:
 * Simpler
 * Deterministic
Cons:
 * Its speed decreases as the number of random strings approaches
   capacity, e.g. for 7 alphanumeric short URLs it's around 37^7. Once
   we start having collisions the lookup time will significantly impact
   the speed at which short URLs are returned

Method 2: pool of short URLs.

Pros:
 * Scales better
 * Faster
Cons:
 * Tricky to implement correctly
 * Requires fine-tuning of producer thresholds to optimise

When length of Url DB approaches capacity OR random strings are found to be non unique more than N times consecutively, then add one char to string length or start expiring old URLs (requires reverse-searching hash db)
