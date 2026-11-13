```json
{
  "id": "dsa-tag-count",
  "kind": "dsa",
  "title": "Top tags",
  "topic": "heaps",
  "tests": [
    {
      "args": [
        [],
        2
      ],
      "expected": []
    },
    {
      "args": [
        [
          "b",
          "a",
          "b",
          "a",
          "c"
        ],
        2
      ],
      "expected": [
        "a",
        "b"
      ]
    },
    {
      "args": [
        [
          "x"
        ],
        0
      ],
      "expected": []
    },
    {
      "args": [
        [
          "z",
          "b",
          "a"
        ],
        5
      ],
      "expected": [
        "a",
        "b",
        "z"
      ]
    },
    {
      "args": [
        [
          "x",
          "x",
          "y"
        ],
        1
      ],
      "expected": [
        "x"
      ]
    }
  ],
  "reference": "def solve(tags, k):\n    from collections import Counter\n    counts = Counter(tags)\n    return sorted(counts, key=lambda x: (-counts[x],x))[:k]\n"
}
```

Return up to k distinct tags ordered by descending frequency, then lexicographically ascending on ties. k is nonnegative. Write solve(tags, k).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
