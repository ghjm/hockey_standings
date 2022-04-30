#!/bin/env python3

import sys
import os
import io
import datetime
import urllib.request
import json
import collections
import webbrowser
import pathlib

import jinja2
import plotly.graph_objects as go
import pytz


season = "20212022"
games_per_season = 82
main_title = "NHL Magic/Tragic Standings"
nhl_copyright = ""


def do_update():
    print("Retrieving standings...")
    with urllib.request.urlopen(
            f"https://statsapi.web.nhl.com/api/v1/standings?season={season}&expand=standings.record") as url:
        data = json.loads(url.read().decode('utf-8'))

    print("Processing downloaded standings...")
    global nhl_copyright
    nhl_copyright = data['copyright']

    conferences = collections.defaultdict(set)
    divisions = collections.defaultdict(list)
    teams = collections.defaultdict(dict)
    for d in data['records']:
        for t in d['teamRecords']:
            tn = t['team']['name']
            divisions[d['division']['name']].append(tn)
            conferences[d['conference']['name']].add(d['division']['name'])
            teams[tn]['pts'] = t['points']
            teams[tn]['gp'] = t['gamesPlayed']
            teams[tn]['pnp'] = 2 * (games_per_season - teams[tn]['gp'])
            teams[tn]['pp'] = teams[tn]['pts'] + teams[tn]['pnp']
            if 'records' in t:
                for r in t['records']['overallRecords']:
                    if r['type'] == 'lastTen':
                        teams[tn]['l10pts'] = 2 * r['wins'] + r['ot']
            if teams[tn]['gp'] > 0:
                teams[tn]['pace'] = float(games_per_season) * float(teams[tn]['pts']) / float(teams[tn]['gp'])
                if 'l10pts' in teams[tn]:
                    teams[tn]['l10pace'] = (
                            float(teams[tn]['pts']) + (
                                float(games_per_season - teams[tn]['gp']) *
                                float(teams[tn]['l10pts']) / min(10.0, teams[tn]['gp'])
                                )
                            )

    print("Finding conference wildcard thresholds...")
    clinch = {'pp': dict(), 'pts': dict(), 'pace': dict()}
    for stat in clinch:
        for c in conferences:
            division_leaders = list()
            wildcard_contenders = list()
            for d in conferences[c]:
                for ct in [t for t in sorted(divisions[d], key=lambda x: teams[x][stat], reverse=True)[:3]]:
                    division_leaders.append(ct)
                for ct in [t for t in sorted(divisions[d], key=lambda x: teams[x][stat], reverse=True)[3:]]:
                    wildcard_contenders.append(ct)
            division_leaders = sorted(division_leaders, key=lambda x: teams[x][stat], reverse=True)
            worst_division_leader = teams[division_leaders[-1]][stat]
            wildcard_contenders = sorted(wildcard_contenders, key=lambda x: teams[x][stat], reverse=True)
            if stat == 'pts':
                clinch[stat][c] = min(worst_division_leader, teams[wildcard_contenders[1]][stat])
            elif stat == 'pp':
                clinch[stat][c] = min(worst_division_leader, teams[wildcard_contenders[2]][stat])
            elif stat == 'pace':
                clinch[stat][c] = (teams[wildcard_contenders[1]][stat] + teams[wildcard_contenders[2]][stat]) / 2

    print("Generating figure...")
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
        dragmode=False,
    )
    sorted_divisions = [(c, d) for c in sorted(conferences) for d in sorted(conferences[c])]
    fig.set_subplots(rows=len(sorted_divisions), cols=1, row_titles=[d for c, d in sorted_divisions])
    rowcount = 1
    for c, d in sorted_divisions:
        dteams = divisions[d]
        fig.update_xaxes(fixedrange=True, row=rowcount, col=1)
        fig.update_yaxes(fixedrange=True, row=rowcount, col=1, showgrid=True)
        sorted_teams = sorted(dteams, key=lambda x: teams[x]['pts'])
        fig.add_trace(go.Bar(
            y=[t for t in sorted_teams],
            x=[teams[t]['pts'] - (0.15 if teams[t]['pnp'] == 0 else 0) for t in sorted_teams],
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
            x=[max(teams[t]['pnp'], 0.3) for t in sorted_teams],
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
            x=[teams[t]['l10pace'] if 'l10pace' in teams[t] else None for t in sorted_teams],
            name='Last 10 Pace',
            orientation='h',
            mode="markers",
            marker=dict(
                color='rgba(212, 232, 79, 1.0)',
            ),
            showlegend=(rowcount == 1),
            legendgroup="l10pace",
            hoverinfo="text",
            hovertext=[f"{t}: Last 10 Pace {teams[t]['l10pace']:.1f}" if 'l10pace' in teams[t] else None
                       for t in sorted_teams]
        ),
            row=rowcount,
            col=1,
        )
        fig.add_trace(go.Scatter(
            y=[t for t in sorted_teams],
            x=[teams[t]['pace'] if 'pace' in teams[t] else None for t in sorted_teams],
            name='Season Pace',
            orientation='h',
            mode="markers",
            marker=dict(
                color='rgba(66, 42, 0, 1.0)',
            ),
            showlegend=(rowcount == 1),
            legendgroup="pace",
            hoverinfo="text",
            hovertext=[f"{t}: Season Pace {teams[t]['pace']:.1f}" if 'pace' in teams[t] else None
                       for t in sorted_teams]
        ),
            row=rowcount,
            col=1,
        )

        fig.add_vline(x=clinch['pts'][c], row=rowcount, col=1)
        if clinch['pp'][c] > clinch['pts'][c]:
            fig.add_vline(x=clinch['pp'][c], row=rowcount, col=1)
        if clinch['pts'][c] < clinch['pace'][c] < clinch['pp'][c]:
            fig.add_vline(x=clinch['pace'][c], row=rowcount, col=1, line_dash="dash", line_width=1)
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
    span = max_pts - min_pts
    dtick = 1
    while (span / dtick) > 40:
        dtick *= 2
    fig.update_xaxes(range=[min_pts - 1, max_pts + 1], side="top", dtick=dtick)
    fig.update_yaxes(dtick=1)

    fig.add_trace(go.Scatter(
        y=[None],
        x=[None],
        name='Clinching Threshold',
        orientation='h',
        mode="markers",
        marker=dict(
            color='rgba(212, 232, 79, 1.0)',
            symbol='line-ns',
            line_width=2,
            size=12,
        ),
        showlegend=True,
        legendgroup="thresh",
    ),
        row=1,
        col=1,
    )

    fig.add_trace(go.Scatter(
        y=[None],
        x=[None],
        name='Season Pace Threshold',
        orientation='h',
        mode="markers",
        marker=dict(
            color='rgba(212, 232, 79, 1.0)',
            symbol='line-ns',
            line_width=1,
            size=6,
        ),
        showlegend=True,
        legendgroup="thresh",
    ),
        row=1,
        col=1,
    )

    fig.add_trace(go.Scatter(
        y=[None],
        x=[None],
        name='Elimination Threshold',
        orientation='h',
        mode="markers",
        marker=dict(
            color='rgba(212, 232, 79, 1.0)',
            symbol='line-ns',
            line_width=2,
            size=12,
        ),
        showlegend=True,
        legendgroup="thresh",
    ),
        row=1,
        col=1,
    )

    return fig


def main():
    print("Generating graphs...")
    fig = do_update()
    print("Generating HTML...")
    scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
    htmlfilename = os.path.join(scriptdir, "index.html")
    with io.StringIO() as pf, open(htmlfilename, "w", encoding="utf-8") as hf:

        fig.write_html(
            file=pf,
            config={"displayModeBar": False},
            include_plotlyjs="cdn",
            include_mathjax="cdn",
            full_html=False,
            auto_open=False,
        )

        tz = pytz.timezone('US/Eastern')
        google_analytics_id = os.environ['GOOGLE_ANALYTICS_ID'] if 'GOOGLE_ANALYTICS_ID' in os.environ else None

        templatefilename = os.path.join(scriptdir, "index.html.j2")
        template = jinja2.Template(open(templatefilename).read())

        hf.write(template.render(
            main_title=main_title,
            main_graph=pf.getvalue(),
            last_update_time=datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z"),
            nhl_copyright=nhl_copyright,
            google_analytics_id=google_analytics_id,
        ))

        # if 'POPUP_IN_LOCAL_BROWSER' in os.environ and os.environ['POPUP_IN_LOCAL_BROWSER']:
        webbrowser.open(pathlib.Path(htmlfilename).as_uri())


if __name__ == "__main__":
    main()
    print("Done.")
