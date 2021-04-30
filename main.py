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
import markdown
import pytz


season = "20202021"
games_per_season = 56
main_title = "NHL Magic/Tragic Standings"
nhl_copyright = ""


def do_update():
    with urllib.request.urlopen(
            f"https://statsapi.web.nhl.com/api/v1/standings?season={season}&expand=standings.record") as url:
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
            teams[tn]['pnp'] = 2 * (games_per_season - teams[tn]['gp'])
            teams[tn]['pp'] = teams[tn]['pts'] + teams[tn]['pnp']
            if 'records' in t:
                for r in t['records']['overallRecords']:
                    if r['type'] == 'lastTen':
                        teams[tn]['l10pts'] = 2 * r['wins'] + r['ot']
            if teams[tn]['gp'] > 0 and teams[tn]['pnp'] > 0:
                teams[tn]['pace'] = float(games_per_season) * float(teams[tn]['pts']) / float(teams[tn]['gp'])
                if 'l10pts' in teams[tn]:
                    teams[tn]['l10pace'] = float(teams[tn]['pts']) + (float(games_per_season - teams[tn]['gp']) *
                                                                      float(teams[tn]['l10pts']) / 10.0)

    with urllib.request.urlopen(f"https://statsapi.web.nhl.com/api/v1/schedule?season={season}") as url:
        seasondata = json.loads(url.read().decode('utf-8'))

    schedule = list()
    for d in sorted(seasondata['dates'], key=lambda x: x['date']):
        date = d['date']
        for g in d['games']:
            if g['status']['abstractGameState'] != 'Final':
                schedule.append((g['teams']['home']['team']['name'], g['teams']['away']['team']['name']))

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
    sorted_divisions = sorted(divisions)
    fig.set_subplots(rows=len(sorted_divisions), cols=1, row_titles=[d for d in sorted_divisions])
    rowcount = 1
    for d in sorted_divisions:
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

        standings = [(t, teams[t]['pts']) for t in dteams]
        ttc = set()
        sch = [g for g in schedule]
        while len(sch) > 0:
            standings = sorted(standings, key=lambda x: x[1])
            cur_4th, cur_4th_pts = standings[-4]
            for g in [g for g in sch]:
                sch.remove(g)
                g0_idx = None
                g1_idx = None
                for i in range(len(standings)):
                    if standings[i][0] == g[0]:
                        g0_idx = i
                        if g1_idx is not None:
                            break
                    if standings[i][0] == g[1]:
                        g1_idx = i
                        if g0_idx is not None:
                            break
                if g0_idx is None or g1_idx is None:
                    break
                if standings[g0_idx][1] > cur_4th_pts:
                    winner_idx = g0_idx
                    loser_idx = g1_idx
                elif standings[g1_idx][1] > cur_4th_pts:
                    winner_idx = g1_idx
                    loser_idx = g0_idx
                elif standings[g0_idx][1] < standings[g1_idx][1]:
                    winner_idx = g0_idx
                    loser_idx = g1_idx
                else:
                    winner_idx = g1_idx
                    loser_idx = g0_idx
                standings[winner_idx] = (standings[winner_idx][0], standings[winner_idx][1] + 2)
                break
        standings = sorted(standings, key=lambda x: x[1])
        elim_thresh = standings[-4][1]
        sorted_by_pp_teams = sorted(dteams, key=lambda x: teams[x]['pp'])
        clinch_thresh = teams[sorted_by_pp_teams[-5]]['pp']
        fig.add_vline(x=elim_thresh, row=rowcount, col=1)
        if clinch_thresh > elim_thresh:
            fig.add_vline(x=clinch_thresh, row=rowcount, col=1)
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
    fig.update_yaxes(dtick=1)
    return fig


def main():
    try:
        fig = do_update()
    except Exception as e:
        raise
    else:
        scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
        htmlfilename = os.path.join(scriptdir, "index.html")
        with io.StringIO() as pf, io.BytesIO() as mf, open(htmlfilename, "w", encoding="utf-8") as hf:

            fig.write_html(
                file=pf,
                config={"displayModeBar": False},
                include_plotlyjs="cdn",
                include_mathjax="cdn",
                full_html=False,
                auto_open=False,
            )

            mdfilename = os.path.join(scriptdir, "how-this-works.md")
            markdown.markdownFromFile(input=mdfilename, output=mf, encoding="utf-8")

            tz = pytz.timezone('US/Eastern')
            google_analytics_id = os.environ['GOOGLE_ANALYTICS_ID'] if 'GOOGLE_ANALYTICS_ID' in os.environ else None

            templatefilename = os.path.join(scriptdir, "index.html.j2")
            template = jinja2.Template(open(templatefilename).read())

            hf.write(template.render(
                main_title=main_title,
                main_graph=pf.getvalue(),
                last_update_time=datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                how_this_works=mf.getvalue().decode('utf-8'),
                nhl_copyright=nhl_copyright,
                google_analytics_id=google_analytics_id,
            ))

            if 'POPUP_IN_LOCAL_BROWSER' in os.environ and os.environ['POPUP_IN_LOCAL_BROWSER']:
                webbrowser.open(pathlib.Path(htmlfilename).as_uri())


if __name__ == "__main__":
    main()
