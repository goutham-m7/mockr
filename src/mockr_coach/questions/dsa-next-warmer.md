```json
{
  "id": "dsa-next-warmer",
  "kind": "dsa",
  "title": "Next higher reading",
  "topic": "monotonic-stack",
  "tests": [
    {
      "args": [
        []
      ],
      "expected": []
    },
    {
      "args": [
        [
          2,
          2,
          3
        ]
      ],
      "expected": [
        2,
        1,
        0
      ]
    },
    {
      "args": [
        [
          3,
          2,
          1
        ]
      ],
      "expected": [
        0,
        0,
        0
      ]
    },
    {
      "args": [
        [
          1,
          4,
          2,
          3
        ]
      ],
      "expected": [
        1,
        0,
        1,
        0
      ]
    },
    {
      "args": [
        [
          -2,
          -1,
          0
        ]
      ],
      "expected": [
        1,
        1,
        0
      ]
    }
  ],
  "reference": "def solve(readings):\n    stack = []\n    result = [0]*len(readings)\n    for i,x in enumerate(readings):\n        while stack and readings[stack[-1]] < x:\n            j = stack.pop(); result[j] = i-j\n        stack.append(i)\n    return result\n"
}
```

For each reading return the number of positions until a strictly higher reading, or 0 if none. Write solve(readings).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
