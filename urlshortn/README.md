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

In both instances a worker receives a long URL to shorten. It calculates
its hash so that it can return the same short URL for the same
original URL. If 

    Hash DB: k/v store (hash -> short URL)

Worker polls hash DB. If present, returns short URL. 

Then - solution A
-----------------
If not, worker generates random string.

    Url DB: k/v store (short URL -> long URL)

[atomic operation starts]
Worker polls Url DB. If present, worker generates another URL.
If not, worker adds entry in Url DB.
[atomic opertion ends]

Then - solution B
-----------------

    Pool: (linked) list of strings; supports POP, PUSH and LENGTH

If not, workers POPs random string from pool.

    Url DB: k/v store (short URL -> long URL)

Worker adds entry in Url DB and Hash DB.

The Pool is a producer/consumer buffer. The producer regularly polls the length of the pool and if it gets below $THRESHOLD it generates random strings. Guarantees uniqueness by checking against Url DB. 

When length of Url DB approaches capacity OR random strings are found to be non unique more than N times consecutively, then add one char to string length or start expiring old URLs (requires reverse-searching hash db)
