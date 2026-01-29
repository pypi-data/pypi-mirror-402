def clamp(value, low, high):
    if low > high:
        raise ValueError("low must be <= high")
    if value < low:
        return low
    if value > high:
        return high
    return value


def mean(nums):
    nums = list(nums)
    if not nums:
        raise ValueError("nums must not be empty")
    return sum(nums) / len(nums)


def percent_change(old, new):
    if old == 0:
        raise ValueError("old must not be 0")
    return ((new - old) / old) * 100.0


def is_even(n):
    return n % 2 == 0
