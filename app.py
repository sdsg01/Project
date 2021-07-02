from logging import debug
import string
from flask import Flask, render_template, url_for, request
import pandas as pd
from werkzeug.utils import redirect
from pyfiles import *

global team1_name
global team2_name

app = Flask(__name__)

#home page 1st
@app.route("/", methods=["GET","POST"])
def index():
    return render_template('home.html')

#teams page
@app.route("/home", methods=["GET","POST"])
def home():
    team1 = []
    team2 = []
    if request.method == "POST":
        print(request.form)
        global team1_name
        team1_name = request.form.get('Team1')
        global team2_name
        team2_name = request.form.get('Team2')

        # # global stadium, city, toss_winner,toss_decision
        # print(request.form)
        # session['Stadium'] = request.form['Stadium']
        # session['City'] = request.form['City']
        # session['Toss Winner'] = request.form['Toss Winner']
        # session['Decision'] = request.form['Decision']
        # print(session)

        t1, t2, t1_roles, t2_roles= get_player_data(team1_name, team2_name)
        t1_len = len(t1)
        t2_len = len(t2)
        return render_template("index.html", t1 = t1, t2 = t2, t1_len =t1_len, t2_len=t2_len,teams = teams, stadiums = stadiums, cities = cities)
    else:
        return render_template("index.html", t1 = team1, t2 = team2, teams = teams, stadiums = stadiums, cities = cities)

#select players page
@app.route('/players/',methods=['GET','POST'])
def players():
    if request.method == "POST":
        print(request.form)
        global team1_name
        team1_name = request.form.get('Team1')
        global team2_name
        team2_name = request.form.get('Team2')

        global stadium, city, toss_winner,toss_decision
        stadium = request.form.get('Stadium')
        city = request.form.get('City')
        toss_winner = request.form.get('Toss Winner')
        toss_decision = request.form.get('Decision')
        print(stadium,city,toss_winner,toss_decision)

        # session['Stadium'] = request.form['Stadium']
        # session['City'] = request.form['City']
        # session['Toss Winner'] = request.form['Toss Winner']
        # session['Decision'] = request.form['Decision']
        # print(session)

        t1, t2, t1_roles, t2_roles = get_player_data(team1_name, team2_name)
        t1_len = len(t1)
        t2_len = len(t2)
        return render_template('players.html', t1 = t1, t2 = t2, t1_len = t1_len, t2_len = t2_len, t1_roles = t1_roles, t2_roles = t2_roles, team1_name = team1_name, team2_name = team2_name)
    else:
        return render_template('home.html')


#response page
@app.route('/response/', methods=['GET','POST'])
def response():
    if request.method == 'POST':
        print(team1_name, team2_name)
        print(request.form)
        print(stadium,city,toss_winner,toss_decision)

        team1_players = request.form.getlist('team1')
        team2_players = request.form.getlist('team2')
        print(team1_players)
        df1 = get_selected_player_data(team1_name, team1_players)
        df2 = get_selected_player_data(team2_name, team2_players)
        df = df1.append(df2)
        data_players = df['player'].to_list()
        data_teams = df['team'].to_list()
        data_credits = df['credit'].to_list()
        data_roles = df['role'].to_list()

        model_input_df = get_model_input(team1_name, team2_name, city, stadium, toss_winner, toss_decision, team1_players, team2_players)
 
        model_output_df = get_model_output_XGB(model_input_df)
        # print(model_output_df)

        #Optimal Lineup
        lp_input = get_lp_input(df,model_output_df)
        lp_output = get_lp_output(lp_input, team1_name, team2_name)
        if type(lp_output) == str:
            #flash(lp_output)
            print(lp_output)
            return render_template('error.html', msg = lp_output)
          
        print(lp_output.columns)
        lpcol = lp_output.columns
        players = lp_output[lpcol[0]]
        lp_teams = lp_output[lpcol[1]]
        points = lp_output[lpcol[2]]
        credits = lp_output[lpcol[3]]
        roles = lp_output[lpcol[4]]
        WK_players = []
        BAT_players = []
        AR_players = []
        BWL_players = []
        t1_players = []
        t2_players = []
        for i, row in lp_output.iterrows():
            if lp_output['team'][i] == team1_name:
                t1_players.append(lp_output['player'][i])
            else:
                # t2_players.append(lp_output[players[i]])
                t2_players.append(lp_output['player'][i])



        for i in range(len(players)):
            if roles[i]=="WK":
                WK_players.append(players[i])
            elif roles[i]=="BAT":
                BAT_players.append(players[i])
            elif roles[i]=="AR":
                AR_players.append(players[i])
            else:
                BWL_players.append(players[i])

        return render_template("response.html", t1_players = t1_players, t2_players = t2_players, data_players = players , len_data = len(players), data_teams = lp_teams, data_points = points, data_credits = credits, team1_name = team1_name, team2_name = team2_name, data_roles = roles, WK_players = WK_players, BAT_players = BAT_players, AR_players = AR_players, BWL_players = BWL_players)
    else:
        return redirect({url_for('error.html')})

if __name__ == "__main__":
    app.run(debug=True)