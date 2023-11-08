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

with st.sidebar:
    st.sidebar.title('Filters')
    all_time = st.sidebar.checkbox('All Matches', value = True)
    if all_time:
        game_time = ''
    else: 
        game_time = st.slider('Input a final game time',20,80,42,1)
    
    regions =  ['WORLD','EUROPE','US EAST','SINGAPORE','US WEST','AUSTRALIA','AUSTRIA','BRAZIL','STOCKHOLM','PW TELECOM SHANGHAI','PW TELECOM ZHEJIANG','PW TELECOM GUANGDONG','JAPAN','PW UNICOM','DUBAI','CHILE']
    
    region = st.sidebar.selectbox('Region', regions)
    if region == 'WORLD':
        region = ''




usefull_columns = [
    'match_id', 'account_id', 'hero_id', 'player_slot', 
    'gold', 'gold_spent', 'gold_per_min', 'xp_per_min', 
    'kills', 'deaths', 'assists', 'hero_damage'
]

df_players = (
    pd.read_csv("players.csv")
    .filter(items=usefull_columns, axis=1)
)

usefull_columns = ['match_id', 'duration', 'radiant_win', 'cluster']
df_matches = (pd.read_csv("match.csv")
            .filter(items = usefull_columns)
)

df_heros = pd.read_csv("hero_names.csv")

columns_to_drop = ['name', 'match_id', 'hero_id', 'player_slot']

df_cluster = pd.read_csv('cluster_regions.csv')

df_merged = (
    pd.merge(df_players,df_heros, how = 'left')
    .merge(df_matches)
    .drop(columns=columns_to_drop)
    .merge(df_cluster, right_on = 'cluster', left_on = 'cluster')
)




df_merged['is_radiant'] = [True if i % 10 < 5 else False for i in range(len(df_merged))]

df_merged["wins"] = df_merged.apply(lambda row: not (row["is_radiant"] ^ row["radiant_win"])  ,axis=1)

df_merged = df_merged.assign(duration = lambda df : (df.duration/60 ).round(2))

if region == '':
    df_merged = df_merged
else:
    df_merged = df_merged.query(f'region == "{region}"')

time = df_merged['duration'].mean().round(2)

if game_time == '':
    df_merged = df_merged
else:
    df_merged = df_merged.query(f'duration > {game_time}')

wins_df = (pd.DataFrame(df_merged['radiant_win'].
                        value_counts(normalize=True)).reset_index())

wins_df = (wins_df.assign(radiant_win=
                        np.select([wins_df['radiant_win']],['Radiant'], 'Dire'))
                        .set_index('radiant_win').round(4)*100)



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


def statiscs_mean(df, games_per_hero):
    
    # Group the original DataFrame by the 'localized_name' column and sum the values for each hero.
    df_grouped_heros_mean = (df.drop(columns = 'region')
                        .groupby('localized_name')
                        .mean()
                        .reset_index()
                        .merge(games_per_hero, on='localized_name')
                        .assign(hero_damage=lambda df: (df.hero_damage).round(2))
                        .assign(wins = lambda df: (df.wins*100).round(2))
                    ).round(2)
    
    return df_grouped_heros_mean

games_per_hero = number_of_matches(df_merged)

df_grouped_heros = statiscs_per_hero(df_merged, games_per_hero)

df_grouped_heros_mean = statiscs_mean(df_merged, games_per_hero)


total_matches = df_merged.shape[0]

## Graficos
def win_rate_plot(df):

    fig = px.bar(df.sort_values('win_rate', ascending = False).head(10), y='win_rate', x='localized_name', text = 'win_rate')
    fig.update_yaxes(showticklabels=False, titlefont = dict(size = 18))
    fig.update_layout(title_text='Win Rate per Hero', xaxis_title= None, yaxis_title = 'Win Rate')
    fig.update_traces(marker_color='darkred')
    fig.update_xaxes(tickangle=45, tickfont=dict(size=14))
    return fig



def hero_statistcs_plots(df , statistc:str, grafic_name:str, y_label:str):
    
    fig = px.bar(df.sort_values(f'{statistc}', ascending = False).head(10),
                y=f'{statistc}',
                x='localized_name',
                text = f'{statistc}')
    
    fig.update_layout(title_text=f'{grafic_name}', xaxis_title= None, yaxis_title = f'{y_label}')
    fig.update_yaxes(showticklabels=False, titlefont = dict(size = 18))
    fig.update_traces(marker_color='darkred')
    fig.update_xaxes(tickangle=45, tickfont=dict(size=14))

    return fig

fig_win_rate_team = px.bar(wins_df.round(2), y='proportion', x=wins_df.index, text = 'proportion')
fig_win_rate_team.update_layout(title_text='Win-Rate per Side', xaxis_title=None, yaxis_title = 'Win-Rate',yaxis_title_font=dict(size=16))
fig_win_rate_team.update_yaxes(showticklabels=False)
fig_win_rate_team.update_traces(textfont_size=16,marker_color='darkred')

fig_win_rate_team.update_xaxes(tickfont=dict(size=16))

plot_win_rate_hero = win_rate_plot(df_grouped_heros)

stats = [ 'gold', 'gold_spent', 'gold_per_min',
        'xp_per_min', 'kills', 'deaths', 'assists', 'hero_damage', 'duration',
        'wins', 'matchs','assists']

aba1, aba2, aba3 = st.tabs(['Win-Rate', 'Statistcs and Results', 'Compare Heros'])


with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total of matches' , total_matches)
        st.plotly_chart(fig_win_rate_team,use_container_width= True)
    with coluna2:
        st.metric('Average game time in minutes' ,time)
        st.plotly_chart(plot_win_rate_hero,use_container_width= True)



with aba2:
        stat =  st.selectbox('Stats', stats)
        fig_stats_heros = hero_statistcs_plots(df_grouped_heros_mean, f'{stat}'   , f'AVERAGE {stat.upper().replace("_", " ")} PER HERO', f'{stat.upper().replace("_", " ")}')
        st.plotly_chart(fig_stats_heros,use_container_width= True  )


heros = df_grouped_heros_mean['localized_name']

with aba3:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        hero1 = st.selectbox('Hero1', heros)
        attributes = df_grouped_heros_mean.query(f'localized_name == "{hero1}"').set_index('localized_name').drop(['account_id', 'is_radiant'], axis=1).T
        for attribute, value in attributes[hero1].items():
            st.metric(label=f'AVERAGE {attribute.replace("_", " ").upper()}', value=value)
    with coluna2:
        hero2 = st.selectbox('Hero2', heros)
        attributes = df_grouped_heros_mean.query(f'localized_name == "{hero2}"').set_index('localized_name').drop(['account_id', 'is_radiant'], axis=1).T
        for attribute, value in attributes[hero2].items():
            st.metric(label=f'AVERAGE {attribute.replace("_", " ").upper()}', value=value)
