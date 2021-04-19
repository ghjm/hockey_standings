#!/bin/env python3

import io
import datetime
import urllib.request
import json
import collections
import plotly.graph_objects as go
import markdown
import pytz


games_per_season = 56
main_title = "NHL Magic/Tragic Standings"
nhl_copyright = ""


def do_update():
    with urllib.request.urlopen("https://statsapi.web.nhl.com/api/v1/standings?expand=standings.record") as url:
        data = json.loads(url.read().decode('utf-8'))

    global nhl_copyright
    nhl_copyright = data['copyright']

    divisions = collections.defaultdict(list)
    teams = collections.defaultdict(dict)
    for d in data['records']:
        for t in d['teamRecords']:
            tn = t['team']['name']
            divisions[d['division']['name']].append(tn)
            teams[tn]['pts'] = t['points']
            teams[tn]['gp'] = t['gamesPlayed']
            teams[tn]['pnp'] = 2 * (games_per_season - t['gamesPlayed'])
            teams[tn]['pp'] = teams[tn]['pts'] + teams[tn]['pnp']
            teams[tn]['pace'] = float(games_per_season) * float(teams[tn]['pts']) / float(teams[tn]['gp'])
            for r in t['records']['overallRecords']:
                if r['type'] == 'lastTen':
                    teams[tn]['l10pts'] = 2 * r['wins'] + r['ot']
            teams[tn]['l10pace'] = \
                float(teams[tn]['pts']) + (float(games_per_season - teams[tn]['gp']) * float(teams[tn]['l10pts']) / 10.0)

    fig = go.Figure()
    fig.update_layout(
        title=main_title,
        title_x=0.5,
        title_font={
            "family": "Helvetica",
            "color": "rgba(19, 0, 66, 1.0)",
            "size": 24,
        },
        barmode='stack',
    )
    fig.set_subplots(rows=len(divisions), cols=1, row_titles=[d for d in divisions])
    rowcount = 1
    for d, dteams in divisions.items():
        sorted_teams = sorted(dteams, key=lambda x: teams[x]['pts'])
        fig.add_trace(go.Bar(
            y=[t for t in sorted_teams],
            x=[teams[t]['pts'] for t in sorted_teams],
            orientation='h',
            marker=dict(
                color='rgba(0, 0, 0, 0)',
            ),
            showlegend=False,
            hoverinfo='skip',
        ),
            row=rowcount,
            col=1,
        )
        fig.add_trace(go.Bar(
            y=[t for t in sorted_teams],
            x=[teams[t]['pnp'] for t in sorted_teams],
            name='Possible Points',
            orientation='h',
            marker=dict(
                color='rgba(0, 66, 37, 0.6)',
                line=dict(color='rgba(0, 66, 37, 1.0)', width=1)
            ),
            showlegend=(rowcount == 1),
            legendgroup="points",
            hoverinfo="text",
            hovertext=[f"{t}: Earned {teams[t]['pts']}, Possible {teams[t]['pp']}" for t in sorted_teams]
        ),
            row=rowcount,
            col=1,
        )
        fig.add_trace(go.Scatter(
            y=[t for t in sorted_teams],
            x=[teams[t]['l10pace'] for t in sorted_teams],
            name='Last 10 Pace',
            orientation='h',
            mode="markers",
            marker=dict(
                color='rgba(212, 232, 79, 1.0)',
            ),
            showlegend=(rowcount == 1),
            legendgroup="l10pace",
            hoverinfo="text",
            hovertext=[f"{t}: Last 10 Pace {teams[t]['l10pace']:.1f}" for t in sorted_teams]
        ),
            row=rowcount,
            col=1,
        )
        fig.add_trace(go.Scatter(
            y=[t for t in sorted_teams],
            x=[teams[t]['pace'] for t in sorted_teams],
            name='Season Pace',
            orientation='h',
            mode="markers",
            marker=dict(
                color='rgba(66, 42, 0, 1.0)',
            ),
            showlegend=(rowcount == 1),
            legendgroup="pace",
            hoverinfo="text",
            hovertext=[f"{t}: Season Pace {teams[t]['pace']:.1f}" for t in sorted_teams]
        ),
            row=rowcount,
            col=1,
        )
        fig.add_vline(x=teams[sorted_teams[-4]]['pts'], row=rowcount, col=1)
        sorted_by_pp_teams = sorted(dteams, key=lambda x: teams[x]['pp'])
        fig.add_vline(x=teams[sorted_by_pp_teams[-4]]['pp'], row=rowcount, col=1)
        rowcount += 1

    min_pts = 9999
    max_pts = 0
    for tn, t in teams.items():
        pts = t['pts']
        if pts < min_pts:
            min_pts = pts
        pp = t['pp']
        if pp > max_pts:
            max_pts = pp
    fig.update_xaxes(range=[min_pts - 1, max_pts + 1], side="top", dtick=2)
    return fig


def main():
    try:
        fig = do_update()
    except Exception as e:
        raise
    else:
        with io.StringIO() as pf, io.BytesIO() as mf, open("index.html", "w") as hf:
            fig.write_html(
                file=pf,
                config={"displayModeBar": False},
                include_plotlyjs="cdn",
                include_mathjax="cdn",
                full_html=False,
            )
            markdown.markdownFromFile(input="how-this-works.md", output=mf, encoding="utf-8")

            tz = pytz.timezone('US/Eastern')

            hf.write("\n".join([
                '<html>',
                '<head>',
                f'<title>{main_title}</title>',
                '<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">',
                '</head>',
                '<body>',
                '<div style="width: 99%; min-width: 600px; height: 92%; min-height: 800px">',
                pf.getvalue(),
                '</div>',
                f'Last Updated: {datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z")}',
                '<hr>',
                '<div style="width: 60%">',
                mf.getvalue().decode('utf-8'),
                '</div>',
                '<hr>',
                '<div style="width: 60%">'
                '<small>',
                'Data feed provided courtesy of the NHL.&nbsp;&nbsp;(Thank you very much, NHL.)',
                f'&nbsp;&nbsp;{nhl_copyright}',
                '</small>',
                '</div>',
                '</body>',
                '</html>']))


if __name__ == "__main__":
    main()
