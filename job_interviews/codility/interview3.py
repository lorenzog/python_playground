# positive integer D is a factor of a positive integer N if there exists an integer M such that N = D * M.
# For example, 6 is a factor of 24, because M = 4 satisfies the above condition (24 = 6 * 4).
# Write a function:
# def solution(N)
# that, given a positive integer N, returns the number of its factors.
# For example, given N = 24, the function should return 8, because 24 has 8 factors, namely 1, 2, 3, 4, 6, 8, 12, 24. There are no other factors of 24.
# Assume that:
# N is an integer within the range [1..2,147,483,647].
# Complexity:
# expected worst-case time complexity is O(sqrt(N));
# expected worst-case space complexity is O(1).
#

def solution ( N ):
    count = 1
    for i in range(1, N):
        if N % i == 0:
            count += 1
    return count

if __name__ == "__main__":
    print(solution(24))
    print(solution(1))
    print(solution(2147483647))

