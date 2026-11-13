```json
{
  "id": "dsa-island-area",
  "kind": "dsa",
  "title": "Island area",
  "topic": "grids",
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
          [
            1
          ]
        ]
      ],
      "expected": 1
    },
    {
      "args": [
        [
          [
            1,
            0
          ],
          [
            0,
            1
          ]
        ]
      ],
      "expected": 1
    },
    {
      "args": [
        [
          [
            1,
            1,
            0
          ],
          [
            0,
            1,
            1
          ]
        ]
      ],
      "expected": 4
    },
    {
      "args": [
        [
          [
            0,
            0
          ]
        ]
      ],
      "expected": 0
    }
  ],
  "reference": "def solve(grid):\n    if not grid or not grid[0]: return 0\n    rows,cols = len(grid),len(grid[0])\n    seen = set(); best = 0\n    for r in range(rows):\n        for c in range(cols):\n            if not grid[r][c] or (r,c) in seen: continue\n            stack = [(r,c)]; seen.add((r,c)); area = 0\n            while stack:\n                x,y = stack.pop(); area += 1\n                for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):\n                    if 0 <= a < rows and 0 <= b < cols and grid[a][b] and (a,b) not in seen:\n                        seen.add((a,b)); stack.append((a,b))\n            best = max(best,area)\n    return best\n"
}
```

Given a rectangular 0/1 grid with four-direction adjacency, return the area of its largest connected island. Empty grids return 0. Do not connect diagonally. Write solve(grid).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
