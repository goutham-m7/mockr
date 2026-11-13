```json
{
  "id": "dsa-batch-search",
  "kind": "dsa",
  "title": "Batch threshold",
  "topic": "binary-search",
  "tests": [
    {
      "args": [
        [],
        4
      ],
      "expected": 0
    },
    {
      "args": [
        [
          3,
          6,
          7
        ],
        6
      ],
      "expected": 3
    },
    {
      "args": [
        [
          10
        ],
        1
      ],
      "expected": 10
    },
    {
      "args": [
        [
          2,
          3
        ],
        1
      ],
      "expected": -1
    },
    {
      "args": [
        [
          1,
          1
        ],
        5
      ],
      "expected": 1
    }
  ],
  "reference": "def solve(batches, capacity):\n    if not batches: return 0\n    if capacity < len(batches): return -1\n    lo,hi = 1,max(batches)\n    while lo < hi:\n        mid = (lo+hi)//2\n        if sum((x+mid-1)//mid for x in batches) <= capacity: hi = mid\n        else: lo = mid+1\n    return lo\n"
}
```

Given positive batch sizes and positive capacity, compute the smallest positive integer processing speed that finishes all batches in capacity time units, each batch taking ceil(size/speed). Return -1 if capacity is smaller than batch count. [] returns 0. Write solve(batches, capacity).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
