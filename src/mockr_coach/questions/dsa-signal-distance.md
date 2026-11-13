```json
{
  "id": "dsa-signal-distance",
  "kind": "dsa",
  "title": "Signal distance",
  "topic": "graphs",
  "tests": [
    {
      "args": [
        1,
        [],
        0,
        0
      ],
      "expected": 0
    },
    {
      "args": [
        3,
        [
          [
            0,
            1
          ],
          [
            1,
            2
          ]
        ],
        0,
        2
      ],
      "expected": 2
    },
    {
      "args": [
        3,
        [
          [
            0,
            1
          ]
        ],
        0,
        2
      ],
      "expected": -1
    },
    {
      "args": [
        4,
        [
          [
            0,
            1
          ],
          [
            0,
            2
          ],
          [
            2,
            3
          ],
          [
            1,
            3
          ]
        ],
        0,
        3
      ],
      "expected": 2
    },
    {
      "args": [
        2,
        [
          [
            0,
            1
          ],
          [
            0,
            1
          ]
        ],
        1,
        0
      ],
      "expected": 1
    }
  ],
  "reference": "def solve(n, edges, source, target):\n    from collections import deque\n    adj = [[] for _ in range(n)]\n    for a,b in edges: adj[a].append(b); adj[b].append(a)\n    queue = deque([(source,0)])\n    seen = {source}\n    while queue:\n        node,d = queue.popleft()\n        if node == target: return d\n        for nxt in adj[node]:\n            if nxt not in seen: seen.add(nxt); queue.append((nxt,d+1))\n    return -1\n"
}
```

An undirected graph has nodes 0..n-1. Return shortest edge distance from source to target, or -1 when unreachable. Edges can repeat. Write solve(n, edges, source, target).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
