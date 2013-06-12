# Two non-negative integers A and B are given. Integer A occurs in integer B at position P if the decimal representation of A is a substring, starting at position P (counting from zero), of the decimal representation of B. Decimal representations are assumed to be big-endian and without leading zeros (the only exception being the number 0, whose decimal representation is "0").
# For example, 53 occurs in 1953786 at position 2. 78 occurs in 195378678 at positions 4 and 7. 57 does not occur in 153786.
# Write a function
# def solution(A,B)
# that, given two non-negative integers A and B, returns the leftmost position at which A occurs in B. The function should return -1 if A does not occur in B.
# For example, given A = 53 and B = 1953786, the function should return 2, as explained above.
# Assume that:
# A is an integer within the range [0..999,999,999];
# B is an integer within the range [0..999,999,999].
# Complexity:
# expected worst-case time complexity is O(log(A)+log(B));
# expected worst-case space complexity is O(log(A)+log(B)).
#

def solution (A, B):
    a_str = str(A)
    b_str = str(B)
    for i in range(0, len(b_str)-len(a_str)):
        sub = b_str[i:i+len(a_str)]
        if a_str == sub:
            return(i)
    return(-1)

if __name__ == "__main__":
    print(solution(53, 1953786))
    print(solution(78, 195378678))
    print(solution(57, 153786))

