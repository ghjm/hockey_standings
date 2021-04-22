### How this works

The green bars show the point standings that a team could possibly end the regular season with.  These bars only
contract, never expand: the left end is the team's current points standing, so it can only move right as more points
are earned.  The right end is the maximum points the team could possibly end the season with, so it can only move
left as games are lost and points become unavailable.

The vertical blue lines show the playoff thresholds.  The line on the left is the elimination mark, and tracks
the current points of the 4th place team in the division.  If a team's green bar falls short of this mark, then
they can never match the points total of the 4th place team, and are eliminated.

The vertical blue line on the right is the clinching threshold.  It tracks the possible points of the 5th place
team - the team you have to beat to make it in.  If a team's green bar is fully to the right of this line, then
they have already earned more points than the 5th place team can possibly end with, so they have clinched a
playoff spot.  If the green bar crosses the line, then the team "controls their own destiny" and can clinch by
just winning enough games, without relying on other teams losing.

In cases where the green bar is exactly touching a line, then tiebreaker rules might matter.  It is possible
for a team to have clinched or been eliminated while touching the line, or not, based on their tiebreaker
standings.  This graph does not attempt to depict any tiebreaker information.

The "Pace" dots show where the team would end the season if their points percentage for their remaining games was the
same as it has been for the season so far ("Season Pace"), or if they maintain the points percentage from their last 10
games ("Last 10 Pace").

Source code for this visualization can be found at [https://github.com/ghjm/NHL_Standings](https://github.com/ghjm/NHL_Standings).
