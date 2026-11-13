```json
{
  "id": "dsa-quiet-window",
  "kind": "dsa",
  "title": "Quiet window",
  "topic": "sliding-window",
  "tests": [
    {
      "args": [
        [],
        0
      ],
      "expected": 0
    },
    {
      "args": [
        [
          4,
          2,
          3,
          8
        ],
        2
      ],
      "expected": 3
    },
    {
      "args": [
        [
          5,
          5,
          5
        ],
        0
      ],
      "expected": 3
    },
    {
      "args": [
        [
          -3,
          -1,
          0
        ],
        2
      ],
      "expected": 2
    },
    {
      "args": [
        [
          1,
          9,
          2,
          3,
          4
        ],
        2
      ],
      "expected": 3
    }
  ],
  "reference": "def solve(readings, limit):\n    from collections import deque\n    lo, hi = deque(), deque()\n    start = best = 0\n    for end, x in enumerate(readings):\n        while lo and readings[lo[-1]] > x: lo.pop()\n        while hi and readings[hi[-1]] < x: hi.pop()\n        lo.append(end); hi.append(end)\n        while readings[hi[0]] - readings[lo[0]] > limit:\n            if lo[0] == start: lo.popleft()\n            if hi[0] == start: hi.popleft()\n            start += 1\n        best = max(best, end-start+1)\n    return best\n"
}
```

Given integer readings and a nonnegative limit, return the length of the longest contiguous window whose maximum minus minimum is at most limit. Empty input returns 0. Write solve(readings, limit).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
