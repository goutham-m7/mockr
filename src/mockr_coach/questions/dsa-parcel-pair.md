```json
{
  "id": "dsa-parcel-pair",
  "kind": "dsa",
  "title": "Parcel pair",
  "topic": "hash-map",
  "tests": [
    {
      "args": [
        [],
        5
      ],
      "expected": []
    },
    {
      "args": [
        [
          2,
          7,
          3
        ],
        9
      ],
      "expected": [
        0,
        1
      ]
    },
    {
      "args": [
        [
          3,
          3
        ],
        6
      ],
      "expected": [
        0,
        1
      ]
    },
    {
      "args": [
        [
          1,
          2,
          1,
          4
        ],
        5
      ],
      "expected": [
        0,
        3
      ]
    },
    {
      "args": [
        [
          -2,
          5,
          0
        ],
        3
      ],
      "expected": [
        0,
        1
      ]
    }
  ],
  "reference": "def solve(weights, target):\n    seen = {}\n    for j, w in enumerate(weights):\n        if target-w in seen: return [seen[target-w], j]\n        seen.setdefault(w,j)\n    return []\n"
}
```

Given integer parcel weights and a target, return indices [i,j], i<j, of the pair with smallest j then smallest i that sums to target; return [] if absent. Write solve(weights, target).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
