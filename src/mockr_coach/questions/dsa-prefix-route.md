```json
{
  "id": "dsa-prefix-route",
  "kind": "dsa",
  "title": "Prefix route",
  "topic": "strings",
  "tests": [
    {
      "args": [
        []
      ],
      "expected": ""
    },
    {
      "args": [
        [
          "/abc",
          "/abd"
        ]
      ],
      "expected": "/ab"
    },
    {
      "args": [
        [
          "same",
          "same"
        ]
      ],
      "expected": "same"
    },
    {
      "args": [
        [
          "",
          "a"
        ]
      ],
      "expected": ""
    },
    {
      "args": [
        [
          "Zoo",
          "zoom"
        ]
      ],
      "expected": ""
    }
  ],
  "reference": "def solve(routes):\n    if not routes: return ''\n    first, last = min(routes), max(routes)\n    i = 0\n    while i < min(len(first),len(last)) and first[i] == last[i]: i += 1\n    return first[:i]\n"
}
```

Return the longest common prefix of a list of case-sensitive route strings. An empty list returns the empty string. Write solve(routes).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
