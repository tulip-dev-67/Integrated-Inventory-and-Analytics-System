"""Search, sort and index algorithms, all written by hand (no sorted(), no heapq)."""
import random


# ---------- Searching ----------

def linear_search(items, predicate):
    """Check every item once; return all that match. O(n)."""
    results = []
    for item in items:
        if predicate(item):
            results.append(item)
    return results


def binary_search_first(sorted_items, target, key):
    """Return the index of the FIRST item whose key equals target, or -1.
    sorted_items must already be sorted by key. O(log n)."""
    low, high = 0, len(sorted_items) - 1
    found = -1
    while low <= high:
        mid = (low + high) // 2
        k = key(sorted_items[mid])
        if k == target:
            found = mid
            high = mid - 1      # keep looking left for an earlier match
        elif k < target:
            low = mid + 1
        else:
            high = mid - 1
    return found


class HashIndex:
    """Maps a key (e.g. SKU or city) to the list of items having it. Lookup is O(1) on average."""

    def __init__(self, items, key):
        self._table = {}
        for item in items:
            self._table.setdefault(key(item), []).append(item)

    def get(self, value):
        return list(self._table.get(value, []))


# ---------- Sorting ----------

def quick_sort(items, key):
    """Quick sort with a random pivot and 3-way split (less / equal / greater).
    The 3-way split matters here: many orders share the same Qty, and a plain
    two-way split would degrade to O(n^2) on that many duplicates."""
    if len(items) <= 1:
        return list(items)
    pivot = key(items[random.randrange(len(items))])
    less, equal, greater = [], [], []
    for item in items:
        k = key(item)
        if k < pivot:
            less.append(item)
        elif k > pivot:
            greater.append(item)
        else:
            equal.append(item)
    return quick_sort(less, key) + equal + quick_sort(greater, key)


def merge_sort(items, key, reverse=False):
    """Stable merge sort: equal keys keep their original relative order."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return _merge(left, right, key, reverse)


def _merge(left, right, key, reverse):
    merged = []
    i = j = 0
    while i < len(left) and j < len(right):
        lk, rk = key(left[i]), key(right[j])
        # '<=' / '>=' take from the LEFT on ties, which is what makes it stable.
        take_left = (lk >= rk) if reverse else (lk <= rk)
        if take_left:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


# ---------- Heap (top N) ----------

def _sift_up(heap, i):
    while i > 0:
        parent = (i - 1) // 2
        if heap[i][0] < heap[parent][0]:
            heap[i], heap[parent] = heap[parent], heap[i]
            i = parent
        else:
            break


def _sift_down(heap, i, size):
    while True:
        smallest = i
        left, right = 2 * i + 1, 2 * i + 2
        if left < size and heap[left][0] < heap[smallest][0]:
            smallest = left
        if right < size and heap[right][0] < heap[smallest][0]:
            smallest = right
        if smallest == i:
            break
        heap[i], heap[smallest] = heap[smallest], heap[i]
        i = smallest


def heap_top_n(items, n, key):
    """Return the n items with the largest key, biggest first.
    Keeps a min-heap of size n: the smallest of the current top n sits at the root,
    so a new item only needs to beat the root to get in. O(m log n) for m items."""
    if n <= 0:
        return []
    heap = []
    for item in items:
        entry = (key(item), item)
        if len(heap) < n:
            heap.append(entry)
            _sift_up(heap, len(heap) - 1)
        elif entry[0] > heap[0][0]:
            heap[0] = entry
            _sift_down(heap, 0, len(heap))
    # Heap sort step: repeatedly move the root (smallest) to the end.
    # A min-heap sorted this way ends up in descending order.
    size = len(heap)
    while size > 1:
        heap[0], heap[size - 1] = heap[size - 1], heap[0]
        size -= 1
        _sift_down(heap, 0, size)
    return [entry[1] for entry in heap]