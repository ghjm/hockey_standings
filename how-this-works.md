### How this works

The green bars show the point standings that a team could possibly end the regular season with.  These bars only
contract, never expand: the left end is the team's current points standing, so it can only move right as more points
are earned.  The right end is the maximum points the team could possibly end the season with, so it can only move
left as games are lost and points become unavailable.

The vertical blue lines show the playoff thresholds.  The line on the left is the elimination mark, and tracks
the current points of the 4th place team in the division, with a possible adjustment if the remaining schedule
forces some team to earn more points than the current 4th place team.  If a team's green bar falls short of this
mark, then they are eliminated.  The line on the right is the clinching threshold, which tracks the maximum 
possible points of the team just outside the last wildcard spot - the team you have to beat to make the playoffs.

The "Pace" dots show where the team would end the season if their points percentage for their remaining games was the
same as it has been for the season so far ("Season Pace"), or if they maintain the points percentage from their last 10
games ("Last 10 Pace").

Source code for this visualization can be found at [https://github.com/ghjm/hockey_standings](https://github.com/ghjm/hockey_standings).
