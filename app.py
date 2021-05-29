from logging import debug
from flask import Flask, render_template, url_for, request
import pandas as pd
from werkzeug.utils import redirect

teams = {'CSK':'Chennai Super Kings', 'MI': 'Mumbai Indians', 'RCB': 'Royal Challengers Banglore', 'RR': 'Rajasthan Royals', 'KKR': 'Kolkata Knight Riders', 'DC': 'Delhi Capitals', 'KXIP':'Kings XI Punjab', 'SRH':'Sunrisers Hyderabad'}
stadiums = ['M Chinnaswamy Stadium',
       'Punjab Cricket Association Stadium, Mohali', 'Feroz Shah Kotla',
       'Wankhede Stadium', 'Eden Gardens', 'Sawai Mansingh Stadium',
       'Rajiv Gandhi International Stadium, Uppal',
       'MA Chidambaram Stadium, Chepauk', 'Dr DY Patil Sports Academy',
       'Newlands', "St George's Park", 'Kingsmead', 'SuperSport Park',
       'Buffalo Park', 'New Wanderers Stadium', 'De Beers Diamond Oval',
       'OUTsurance Oval', 'Brabourne Stadium',
       'Sardar Patel Stadium, Motera', 'Barabati Stadium',
       'Vidarbha Cricket Association Stadium, Jamtha',
       'Himachal Pradesh Cricket Association Stadium', 'Nehru Stadium',
       'Holkar Cricket Stadium',
       'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium',
       'Subrata Roy Sahara Stadium',
       'Shaheed Veer Narayan Singh International Stadium',
       'JSCA International Stadium Complex', 'Sheikh Zayed Stadium',
       'Sharjah Cricket Stadium', 'Dubai International Cricket Stadium',
       'Maharashtra Cricket Association Stadium',
       'Punjab Cricket Association IS Bindra Stadium, Mohali',
       'Saurashtra Cricket Association Stadium', 'Green Park',
       'M.Chinnaswamy Stadium']

cities = ['Bangalore', 'Chandigarh', 'Delhi', 'Mumbai', 'Kolkata', 'Jaipur',
       'Hyderabad', 'Chennai', 'Cape Town', 'Port Elizabeth', 'Durban',
       'Centurion', 'East London', 'Johannesburg', 'Kimberley',
       'Bloemfontein', 'Ahmedabad', 'Cuttack', 'Nagpur', 'Dharamsala',
       'Kochi', 'Indore', 'Visakhapatnam', 'Pune', 'Raipur', 'Ranchi',
       'Abu Dhabi', 'Sharjah', 'Dubai', 'Rajkot', 'Kanpur']

global team1_name
global team2_name

def get_player_data(t1, t2):
    df = pd.read_csv('F:\FINAL YEAR BTech\BE PROJECT\Project\dataset\players.csv')
    team1_players = df[t1].to_list()
    team2_players = df[t2].to_list()
    # credit1 = t1 +"_credits"
    # credit2 = t2 +"_credits"
    # team1_credits = df[credit1].to_list()
    # team2_credits = df[credit2].to_list()
    # role1 = t1 +"_player_role"
    # role2 = t2 +"_player_role"
    # team1_role = df[role1].to_list()
    # team2_role = df[role2].to_list()

    # return team1_players, team2_players, team1_credits, team2_credits, team1_role, team2_role
    return team1_players, team2_players

def get_selected_player_data(team, team_players):
    df = pd.read_csv('F:\FINAL YEAR BTech\BE PROJECT\Project\dataset\players.csv')
    res = pd.DataFrame(columns = ['player', 'team','credit', 'role'])
    for players in team_players:
        expr = team + "=="+ "\""+ players + "\"" 
        temp = df.query(str(expr))
        tc = team+"_credits"
        tr = team+"_player_role"
        lst = [temp[team].item(), temp[team].name, temp[tc].item(), temp[tr].item()]
        # print(lst)
        a_series = pd.Series(lst, index = res.columns)
        res = res.append(a_series, ignore_index=True)
    return res


app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def home():
    team1 = []
    team2 = []
    if request.method == "POST":
        global team1_name
        team1_name = request.form.get('Team1')
        global team2_name
        team2_name = request.form.get('Team2')
        # t1,t2,t1_cred, t2_cred, t1_role, t2_role = get_player_data(team1_name, team2_name)
        t1, t2 = get_player_data(team1_name, team2_name)
        return render_template("index.html", t1 = t1, t2 = t2, teams = teams, stadiums = stadiums, cities = cities)
    else:
        return render_template("index.html", t1 = team1, t2 = team2, teams = teams, stadiums = stadiums, cities = cities)

@app.route('/response/', methods=['GET','POST'])
def response():
    if request.method == 'POST':
        # print(team1_name, team2_name)
        team1_players = request.form.getlist('team1')
        team2_players = request.form.getlist('team2')
        df1 = get_selected_player_data(team1_name, team1_players)
        df2 = get_selected_player_data(team2_name, team2_players)
        df = df1.append(df2)
        data_players = df['player'].to_list()
        data_teams = df['team'].to_list()
        data_credits = df['credit'].to_list()
        data_roles = df['role'].to_list()

        return render_template("response.html", data_players= data_players, len_data = len(data_players), data_teams= data_teams, data_credits=data_credits, data_roles=data_roles)
    else:
        return redirect({url_for('home')})

if __name__ == "__main__":
    app.run(debug=True)