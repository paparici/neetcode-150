"""217. Contains Duplicate

https://leetcode.com/problems/contains-duplicate/
"""


def contains_duplicate(nums: list[int]) -> bool:
    """Return True if any value appears at least twice in ``nums``.

    Time: O(n), each element is looked up and inserted at most once.
    Space: O(n), the set may hold every element.
    """
    seen: set[int] = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
