"""
/**
 * http://stackoverflow.com/q/2553522/204634
 *
Given two string s1 and s2 how will you check if s1 is a rotated version of s2 ?

Example:

If s1 = "stackoverflow" then the following are some of its rotated versions:

"tackoverflows"
"ackoverflowst"
"overflowstack"

where as "stackoverflwo" is not a rotated version.

 *
 */
"""

# python version :)

a = "stackoverflow"
b = "ackoverflowst"
c = "stackoverflwo" 

def check(orig, rotated):
    z = orig+orig
    print(rotated, "is")
    if rotated not in z:
        print(" not ")
    print("a rotated version of", orig)

check(a, b)
check(a, c)
