import json

import pandas as pd
import requests
import dash
from dash import dcc, html
from dash import dash_table as table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

req = requests.get('https://statsapi.web.nhl.com/api/v1/teams')
data = req.json()

teams = {team['id']: team['name'] for team in data['teams']}

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

layout = html.Div([
    html.H1('Select Team'),
    dcc.Dropdown(
        id='team-select',
        options=[
            {'label':name, 'value':key} for key, name in teams.items()
        ],
        value='15'
    ),
    dbc.Row([
        dbc.Col(id='table-div', width=8),
        dbc.Col(id='player-info', width=4)
    ]),
])

@app.callback(
    [Output('table-div', 'children')],
    [Input('team-select', 'value')]
)
def roster_table(id):
    roster = requests.get(f'https://statsapi.web.nhl.com/api/v1/teams/{id}/roster').json()['roster']
    col_names = ['name', 'number', 'position']
    cols = [{'name': i, 'id': i} for i in col_names]
    table_roster = []

    for player in roster:
        p_dict = {}
        p_dict['name'] = player['person']['fullName']
        p_dict['number'] = player['jerseyNumber']
        p_dict['position'] = player['position']['name']
        p_dict['id'] = player['person']['id']
        table_roster.append(p_dict)

    rtable = table.DataTable(
        id='roster-table',
        columns=cols,
        data=table_roster
    )

    return [rtable]


@app.callback(
    [Output('player-info', 'children')],
    [Input('roster-table', 'active_cell')],
    [State('team-select', 'value')]
)
def player_info(cell, team):
    player_id = cell['row_id']

    req = requests.get(f'https://statsapi.web.nhl.com/api/v1/people/{player_id}/stats?stats=statsSingleSeason')
    stats = req.json()['stats'][0]
    req = requests.get(f'https://statsapi.web.nhl.com/api/v1/people/{player_id}')
    info = req.json()
    info_colnames = ['number', 'position', 'hometown', 'age']
    basic_colnames = ['points', 'goals', 'assists', 'shots', 'hits', 'PPP', 'games']
    toi_colnames = ['TOI', 'Even', 'PP', 'PK']
    info_cols = [{'name': i, 'id': i} for i in info_colnames]
    basic_cols = [{'name': col, 'id': col} for col in basic_colnames]
    toi_cols = [{'name': col, 'id': col} for col in toi_colnames]

    number = info['people'][0]['primaryNumber']
    position = info['people'][0]['primaryPosition']['abbreviation']
    hometown = info['people'][0]['birthStateProvince']
    age = info['people'][0]['currentAge']

    stats_dict = {}
    stats_dict['goals'] = stats['splits'][0]['stat']['goals']
    stats_dict['assists'] = stats['splits'][0]['stat']['assists']
    stats_dict['points'] = stats_dict['goals'] + stats_dict['assists']
    stats_dict['shots'] = stats['splits'][0]['stat']['shots']
    stats_dict['hits'] = stats['splits'][0]['stat']['hits']
    stats_dict['PPP'] = stats['splits'][0]['stat']['powerPlayPoints']
    stats_dict['games'] = stats['splits'][0]['stat']['games']

    toi_dict = {}
    toi_dict['TOI'] = stats['splits'][0]['stat']['timeOnIcePerGame']
    toi_dict['Even'] = stats['splits'][0]['stat']['evenTimeOnIcePerGame']
    toi_dict['PP'] = stats['splits'][0]['stat']['powerPlayTimeOnIcePerGame']
    toi_dict['PK'] = stats['splits'][0]['stat']['shortHandedTimeOnIcePerGame']

    data = [{'number':number,'position':position,'hometown':hometown,'age':age}]
    basic_data = [stats_dict]
    toi_data = [toi_dict]

    layout = html.Div([
        html.H1(info['people'][0]['fullName']),
        table.DataTable(
            columns=info_cols,
            data=data
        ),
        html.H2('Basic stats'),
        html.P(
          table.DataTable(
              columns=basic_cols,
              data=basic_data
          )
        ),
        html.H2('TOI'),
        table.DataTable(
            columns=toi_cols,
            data=toi_data
        )
    ])

    return [layout]

app.layout = layout

app.run_server(debug=True)
