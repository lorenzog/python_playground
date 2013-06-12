# A string is a palindrome if it has exactly the same sequence of characters when read left-to-right as it has when read right-to-left. For example, the following strings are palindromes:
# "kayak",
# "codilitytilidoc",
# "neveroddoreven".
# A string A is an anagram of a string B if A can be obtained from B by rearranging the characters. For example, in each of the following pairs one string is an anagram of the other:
# "mary" and "army",
# "rocketboys" and "octobersky",
# "codility" and "codility".
# Write a function:
# def solution(S)
# that, given a non-empty string S consisting of N characters, returns 1 if S is an anagram of some palindrome and returns 0 otherwise.
# Assume that:
# N is an integer within the range [1..100,000];
# string S consists only of lower-case letters (a-z)
# For example, given S = "dooernedeevrvn", the function should return 1, because "dooernedeevrvn" is an anagram of the palindrome "neveroddoreven". Given S = "aabcba", the function should return 0.
# Complexity:
# expected worst-case time complexity is O(N);
# expected worst-case space complexity is O(1) (not counting the storage required for input arguments).
#

def solution ( S ):
    flips = dict()
    num_flips = 0

    if len(S) == 1:
        return 1

    for c in S:
        if c in flips:
            if flips[c] == 0:
                flips[c] = 1
            else:
                flips[c] = 0
        else:
            flips.update({c: 1})

    for item in flips.values():
        if item == 1:
            num_flips += 1

    if len(S) % 2 == 0:
        # even
        print('even')
        if num_flips == 0:
            return 1
        else:
            return 0
    else:
        # odd
        print('odd')
        if num_flips == 1:
            return 1
        else:
            return 0

if __name__ == "__main__":
    print('dooernedeevrvn:', solution('dooernedeevrvn'))
    print('neveroddoreven:', solution('neveroddoreven'))
    

# go through S (string)
# S == 1 return 1
# for each letter in S, 
# set [letter] to 1 if it was 0, to 0 if it was 1
# if N odd, only one [letter] must be set to 1
# if N even, no [letter] must be set to 1
