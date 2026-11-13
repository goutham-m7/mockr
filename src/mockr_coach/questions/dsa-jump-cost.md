```json
{
  "id": "dsa-jump-cost",
  "kind": "dsa",
  "title": "Jump cost",
  "topic": "dynamic-programming",
  "tests": [
    {
      "args": [
        []
      ],
      "expected": 0
    },
    {
      "args": [
        [
          7
        ]
      ],
      "expected": 7
    },
    {
      "args": [
        [
          3,
          100,
          2
        ]
      ],
      "expected": 5
    },
    {
      "args": [
        [
          1,
          2,
          3,
          4
        ]
      ],
      "expected": 7
    },
    {
      "args": [
        [
          0,
          0,
          0
        ]
      ],
      "expected": 0
    }
  ],
  "reference": "def solve(costs):\n    if not costs: return 0\n    if len(costs) == 1: return costs[0]\n    a,b = costs[0], costs[0]+costs[1]\n    for c in costs[2:]: a,b = b,min(a,b)+c\n    return b\n"
}
```

Given nonnegative landing costs, start at index 0 paying its cost and reach the last index using jumps of 1 or 2. Return minimum total cost; [] returns 0. Write solve(costs).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
