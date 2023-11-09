import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

st.set_page_config(layout= 'wide', page_title= 'DOTA2 - Results & Statistcs')
st.title('DOTA 2 - A quick analyse')
st.header('''Walk among the results.''')

## Tables
useful_columns = [
    'match_id', 'account_id', 'hero_id', 'player_slot', 
    'gold', 'gold_spent', 'gold_per_min', 'xp_per_min', 
    'kills', 'deaths', 'assists', 'hero_damage'
]

df_players = (
    pd.read_csv("players.csv")
    .filter(items=useful_columns, axis=1)
)

useful_columns = ['match_id', 'duration', 'radiant_win']
df_matches = (pd.read_csv("match.csv")
            .filter(items = useful_columns)
)

df_heros = pd.read_csv("hero_names.csv")


columns_to_drop = ['name', 'match_id', 'hero_id', 'player_slot']

df_merged = (
    pd.merge(df_players,df_heros, how = 'left')
    .merge(df_matches)
    .drop(columns=columns_to_drop)
)

df_merged = df_merged.assign(duration = lambda df : (df.duration/60 ).round(2))
time = df_merged['duration'].mean().round(2)

wins_df = (pd.DataFrame(df_merged['radiant_win'].
                        value_counts(normalize=True)).reset_index())

wins_df = (wins_df.assign(radiant_win=
                          np.select([wins_df['radiant_win']],['Radiant'], 'Dire'))
                           .set_index('radiant_win').round(4)*100)

# Setting the times considering that every 10 following players are in the same match and the 5 first are radiant e others dire
df_merged['is_radiant'] = [True if i % 10 < 5 else False for i in range(len(df_merged))]

#Creates the "wins" column with True if the "is_radiant" and 'radiant_win are true at the sime time, else False'
df_merged["wins"] = df_merged.apply(lambda row: not (row["is_radiant"] ^ row["radiant_win"])  ,axis=1)

def number_of_matches(df):
    
    games_per_hero = (df.groupby('localized_name')
                      .size()
                      .reset_index(name = 'matchs'))
    
    return games_per_hero

def statiscs_per_hero(df, games_per_hero):
    
    # Group the original DataFrame by the 'localized_name' column and sum the values for each hero.
    df_grouped_heros = (df.groupby('localized_name').sum().reset_index()
                        .merge(games_per_hero, on='localized_name')
                        .assign(duration=lambda df: (df.duration / df.matchs).round(2))
                        .assign(win_rate=lambda df: (df.wins * 100 / df.matchs).round(2))
                        .assign(kill_game=lambda df: (df.kills / df.matchs).round(2))
                        .assign(assists_game=lambda df: (df.assists / df.matchs).round(2))
                        .assign(hero_damage=lambda df: (df.hero_damage / 1000000).round(2))  
                       )
    
    return df_grouped_heros

games_per_hero = number_of_matches(df_merged)

df_grouped_heros = statiscs_per_hero(df_merged, games_per_hero)

games_per_hero_42 = number_of_matches(df_merged.query("duration > 41.26"))

df_grouped_heros_42 = statiscs_per_hero(df_merged.query("duration > 41.26"), games_per_hero_42)



## Graficos
fig_win_rate_team = px.bar(wins_df.round(2), y='proportion', x=wins_df.index, text = 'proportion')
fig_win_rate_team.update_layout(title_text='Win-Rate per Side', xaxis_title=None, yaxis_title = 'Win-Rate',yaxis_title_font=dict(size=16))
fig_win_rate_team.update_yaxes(showticklabels=False)
fig_win_rate_team.update_traces(textfont_size=16)
fig_win_rate_team.update_traces(marker_color='darkred')
fig_win_rate_team.update_xaxes(tickfont=dict(size=16))

def win_rate_plot(df):

    fig = px.bar(df.sort_values('win_rate', ascending = False).head(10), y='win_rate', x='localized_name', text = 'win_rate')

    fig.update_yaxes(showticklabels=False, titlefont = dict(size = 18))

    fig.update_layout(title_text='Win-Rate per Hero', xaxis_title= None, yaxis_title = 'Win-Rate')
    fig.update_traces(marker_color='darkred')
    fig.update_xaxes(tickangle=45, tickfont=dict(size=14))

    return fig

plot_win_rate_hero = win_rate_plot(df_grouped_heros)
plot_win_rate_hero41 = win_rate_plot(df_grouped_heros_42)

list_top_10 = df_grouped_heros.sort_values('win_rate', ascending = False).head(10)['localized_name']
fig_top_10_average = px.bar(df_grouped_heros_42.sort_values('win_rate').query('localized_name in @list_top_10'), y='win_rate', x='localized_name', text = 'win_rate')
fig_top_10_average.update_layout(title_text='Win-Rate per Hero', xaxis_title= None, yaxis_title = 'Win-Rate')
fig_top_10_average.update_yaxes(showticklabels=False)
fig_top_10_average.update_xaxes(categoryorder='array', categoryarray=list_top_10,tickangle=45, tickfont=dict(size=14))
fig_top_10_average.update_traces(marker_color='darkred')


def hero_statistcs_plots(df , statistc:str, grafic_name:str, y_label:str):
    fig = px.bar(df.sort_values(f'{statistc}', ascending = False).head(10), y=f'{statistc}', x='localized_name', text = f'{statistc}')
    fig.update_yaxes(showticklabels=False)
    fig.update_layout(title_text=f'{grafic_name}', xaxis_title= None, yaxis_title = f'{y_label}')
    fig.update_yaxes(showticklabels=False, titlefont = dict(size = 18))
    fig.update_xaxes(tickangle=45, tickfont=dict(size=14))
    fig.update_traces(marker_color='darkred')
    return fig

fig_kills_heros = hero_statistcs_plots(df_grouped_heros, 'kills', 'Kills per Hero', 'Kills')
fig_kills_game = hero_statistcs_plots(df_grouped_heros, 'kill_game', 'Heros kill per game', 'Kills')
fig_damage_hero = hero_statistcs_plots(df_grouped_heros, 'hero_damage', 'Heros damage ', 'Damage - Million ')
fig_assists_hero = hero_statistcs_plots(df_grouped_heros, 'assists_game', 'Heros Assists per game', 'Assists')
#Visualizacao strem

aba1, aba2 = st.tabs(['Win-Rate', 'Statistcs and Results'])

with aba1:

    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total of matches' , '500.000')
        st.header('Win-Rate per Side in all-time matches')
        st.plotly_chart(fig_win_rate_team,use_container_width= True)
        st.header('Games bigger than average time')
        st.plotly_chart(plot_win_rate_hero41, use_container_width= True)

    with coluna2:
        st.metric('Average game time in minutes' ,time)
        st.header('Top 10 Win-Rate heros in all-time matches')
        st.plotly_chart(plot_win_rate_hero,use_container_width= True)
        st.header('Atualized top 10 Win-Rate')
        st.plotly_chart(fig_top_10_average,use_container_width= True )


with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.plotly_chart(fig_kills_heros,use_container_width= True )
        st.plotly_chart(fig_assists_hero ,use_container_width= True )
    with coluna2:
        st.plotly_chart(fig_kills_game,use_container_width= True )
        st.plotly_chart(fig_damage_hero,use_container_width= True )

