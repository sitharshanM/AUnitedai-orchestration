def find_median(numbers):
    """Calculates the median of a single sequence of numbers.
    Raises ValueError if the input list is empty.
    """
    if not numbers:
        raise ValueError("Cannot calculate median of an empty list")
    
    sorted_nums = sorted(numbers)
    n = len(sorted_nums)
    mid = n // 2
    
    if n % 2 == 1:
        return sorted_nums[mid]
    else:
        return (sorted_nums[mid - 1] + sorted_nums[mid]) / 2.0


def findMedianSortedArrays(nums1, nums2):
    """Finds the median of two sorted arrays in logarithmic time complexity."""
    if len(nums1) > len(nums2):
        return findMedianSortedArrays(nums2, nums1)
    
    x, y = len(nums1), len(nums2)
    low, high = 0, x
    
    while low <= high:
        partitionX = (low + high) // 2
        partitionY = (x + y + 1) // 2 - partitionX
    
        maxLeftX = float('-inf') if partitionX == 0 else nums1[partitionX - 1]
        minRightX = float('inf') if partitionX == x else nums1[partitionX]
    
        maxLeftY = float('-inf') if partitionY == 0 else nums2[partitionY - 1]
        minRightY = float('inf') if partitionY == y else nums2[partitionY]
    
        if maxLeftX <= minRightY and maxLeftY <= minRightX:
            # We have the correct partitions
            if (x + y) % 2 == 0:
                return (max(maxLeftX, maxLeftY) + min(minRightX, minRightY)) / 2.0
            else:
                return max(maxLeftX, maxLeftY)
        elif maxLeftX > minRightY:
            high = partitionX - 1
        else:
            low = partitionX + 1
    
    raise ValueError("Input arrays are not sorted or have no elements")
