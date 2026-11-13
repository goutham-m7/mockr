```json
{
  "id": "dsa-room-peak",
  "kind": "dsa",
  "title": "Room peak",
  "topic": "intervals",
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
            1,
            3
          ],
          [
            3,
            5
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
            4
          ],
          [
            2,
            5
          ],
          [
            3,
            6
          ]
        ]
      ],
      "expected": 3
    },
    {
      "args": [
        [
          [
            0,
            1
          ],
          [
            0,
            1
          ]
        ]
      ],
      "expected": 2
    },
    {
      "args": [
        [
          [
            -4,
            -2
          ],
          [
            -3,
            0
          ],
          [
            1,
            2
          ]
        ]
      ],
      "expected": 2
    }
  ],
  "reference": "def solve(intervals):\n    events = sorted((t,d) for a,b in intervals for t,d in ((a,1),(b,-1)))\n    current = best = 0\n    for _, d in events:\n        current += d\n        best = max(best,current)\n    return best\n"
}
```

Given half-open [start,end) meeting intervals with start<end, return the peak number of simultaneous meetings. A room can be reused at the exact end time. Write solve(intervals).

State assumptions, describe your approach before coding, and discuss time and space complexity. Inputs fit in memory; n <= 10000 unless the grid has at most 10000 cells.
