from logging import debug
from flask import Flask, render_template, url_for, request
import pandas as pd
from werkzeug.utils import redirect
import pickle
import pulp
import xgboost

teams = {'CSK':'Chennai Super Kings', 'MI': 'Mumbai Indians', 'RCB': 'Royal Challengers Bangalore', 'RR': 'Rajasthan Royals', 'KKR': 'Kolkata Knight Riders', 'DC': 'Delhi Capitals', 'KXIP':'Kings XI Punjab', 'SRH':'Sunrisers Hyderabad'}
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
    df = pd.read_csv('dataset\players.csv')
    team1_players = df[t1].to_list()
    team2_players = df[t2].to_list()
    return team1_players, team2_players

def get_selected_player_data(team, team_players):
    df = pd.read_csv('dataset\players.csv')
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

        model_input_df = get_model_input(team1_name, team2_name, city, stadium, toss_winner, toss_decision, team1_players, team2_players)
 
        model_output_df = get_model_output_XGB(model_input_df)
        # print(model_output_df)

        #Optimal Lineup
        lp_input = get_lp_input(df,model_output_df)
        lp_output = get_lp_output(lp_input)
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
        return redirect({url_for('home')})

def get_model_input(team1_name, team2_name, city, venue, toss_winner, toss_decision, team1, team2):

    model_df = pd.read_csv("dataset/model_input_data.csv")
    team_label_rl = pickle.load(open("dataset/labels pickled/team_label.sav", 'rb'))
    city_label_rl = pickle.load(open("dataset/labels pickled/city_label.sav", 'rb'))
    venue_label_rl = pickle.load(open("dataset/labels pickled/venue_label.sav", 'rb'))
    toss_decision_label_rl = pickle.load(open("dataset/labels pickled/toss_decision_label.sav", 'rb'))

    num_col = ['finisher', 'running_in_wickets', 'batsman_runs_playername_std3',
       'strike_rate_playername_std3', 'avg_runs_for_wickets',
       'total_wickets_playername_std3', 'econ_rate_playername_std3','points_runs_playername_avg3',
       'balls_faced_playername_avg3', 'points_6s_playername_avg3',
       'points_4s_playername_avg3', 'sr_category_playername_avg3',
       '100_playername_avg3', '50_playername_avg3', '30_playername_avg3',
       'fall_of_wickets_playername_avg3', 'hard_hitting_playername_avg3',
       'balls_bowled_playername_avg3', 'wicket_points_playername_avg3',
       'maiden_points_playername_avg3', 'er_category_playername_avg3',
       'caught_points_playername_avg3', 'wicket_taking_playername_avg3',
       'avg_runs_for_wickets_playername_avg3',
       'stumped_points_playername_avg3', 'runout_points_playername_avg3',
       'total_bat_points_playername_avg3', 'total_bowl_points_playername_avg3',
       'total_field_points_playername_avg3',
       'TOTAL_DREAM_POINTS_playername_avg3', 'total_bat_points_venue_avg3',
       'total_bowl_points_venue_avg3', 'total_field_points_venue_avg3',
       'TOTAL_DREAM_POINTS_venue_avg3']

    cat_col = ['id','playername','Players_team','Opposite_team','city','venue','neutral_venue', 'toss_winner','toss_decision'] 

    model_input = pd.DataFrame(columns=cat_col+num_col)

    id=1 # to change later
    city = city_label_rl.transform([city])[0]
    venue = venue_label_rl.transform([venue])[0]
    neutral_venue = 1
    toss_winner = team_label_rl.transform([teams[toss_winner]])[0]
    toss_decision = toss_decision_label_rl.transform([toss_decision])[0]
    player_team = team_label_rl.transform([teams[team1_name]])[0]
    opposite_team = team_label_rl.transform([teams[team2_name]])[0]

    
    for player in team1:
        player_list = []
        player_list.extend([id, player, player_team, opposite_team, city, venue, neutral_venue, toss_winner, toss_decision])

        #old players
        if player in model_df['playername'].to_list():
            p = model_df[model_df['playername']==player]
            for col in num_col:
                player_list.append(p[col].iloc[-1])
        #new players
        else:
            for n in range(len(num_col)):
                player_list.append(0.0)

        model_input.loc[len(model_input)] = player_list


    player_team = team_label_rl.transform([teams[team2_name]])[0]
    opposite_team = team_label_rl.transform([teams[team1_name]])[0]
 
    for player in team2:
        player_list = []
        player_list.extend([id, player, player_team, opposite_team, city, venue, neutral_venue, toss_winner, toss_decision])

        if player in model_df['playername'].to_list():
            p = model_df[model_df['playername']==player]
            for col in num_col:
                player_list.append(p[col].iloc[-1])
        else:
            for n in range(len(num_col)):
                player_list.append(0.0)

        model_input.loc[len(model_input)] = player_list
    return model_input

def get_model_output_XGB(model_input):

    # XGBRF_model = pickle.load(open("dataset/Models/RF_reg.sav", 'rb')) RF 
    XGBRF_model = pickle.load(open("dataset/Models/CAT_reg.sav", 'rb'))

    # model_xgb = xgboost.XGBRegressor()
    # XGBRF_model = pickle.load(open("dataset/Models/XGB_reg.sav", 'rb'))
    
    check_df = model_input.copy(deep=True)
    model_input.drop(columns=['id','playername'], inplace=True)

    model_input['Players_team'] = pd.to_numeric(model_input['Players_team'])
    model_input['Opposite_team'] = pd.to_numeric(model_input['Opposite_team'])
    model_input['city'] = pd.to_numeric(model_input['city'])
    model_input['venue'] = pd.to_numeric(model_input['venue'])
    model_input['neutral_venue'] = pd.to_numeric(model_input['neutral_venue'])
    model_input['toss_decision'] = pd.to_numeric(model_input['toss_decision'])
    model_input['toss_winner'] = pd.to_numeric(model_input['toss_winner'])

    model_input.fillna(0.0, inplace=True)
    prediction = XGBRF_model.predict(model_input)
    check_df["Predicted"] = prediction
    check = check_df[['playername','Players_team', 'Opposite_team','Predicted']]

    return check

def undummify(df, prefix_sep="_"):
    cols2collapse = {
        item.split(prefix_sep)[0]: (prefix_sep in item) for item in df.columns
    }
    series_list = []
    for col, needs_to_collapse in cols2collapse.items():
        if needs_to_collapse:
            undummified = (
                df.filter(like=col)
                .idxmax(axis=1)
                .apply(lambda x: x.split(prefix_sep, maxsplit=1)[1])
                .rename(col)
            )
            series_list.append(undummified)
        else:
            series_list.append(df[col])
    undummified_df = pd.concat(series_list, axis=1)
    return undummified_df

def get_lp_input(df, model_output_df):
    # print(model_output_df.columns)
    # print(df.columns)
    lp_input = pd.merge(model_output_df,df, left_on='playername', right_on='player',how='left')
    lp_input.drop(['Players_team','Opposite_team','playername'], axis=1, inplace=True)
    lp_input.rename(columns={'Predicted':'points'}, inplace=True)
    lp_input = pd.get_dummies(lp_input, columns=['role','team'])

    return lp_input

def get_lp_output(processed_player_data):
    # Initialize the optimization Problem 
    prob = pulp.LpProblem('Dreamteam', pulp.LpMaximize)

    # selection decision variables can be 0 or 1. The number of `selection_decision_varibales` should be equal to 
    # the number of players under consideration
    selection_decision_variables = []

    for row in processed_player_data.itertuples(index=True):
        variable_name = 'x_{}'.format(str(row.Index))
        variable = pulp.LpVariable(variable_name, lowBound = 0, upBound = 1, cat = 'Integer' ) 
        selection_decision_variables.append({"pulp_variable":variable, "player": row.player})
    
    selection_decision_variables_df = pd.DataFrame(selection_decision_variables)

    merged_processed_player_df = pd.merge(processed_player_data, selection_decision_variables_df, 
                                                    on = "player")
    merged_processed_player_df["pulp_variable_name"] = merged_processed_player_df["pulp_variable"].apply(lambda x: x.name)

    # Create the objective Function to be maximized

    total_points = pulp.lpSum(merged_processed_player_df["points"] * selection_decision_variables_df["pulp_variable"])
    prob += total_points

    # 1 <= n_keeper <= 4 
    total_keepers = pulp.lpSum(merged_processed_player_df["role_WK"] * selection_decision_variables_df["pulp_variable"])
    prob += (total_keepers >= 1)
    prob += (total_keepers <= 4)

    # 3 <= n_batsmen <= 6 
    total_batsmen = pulp.lpSum(merged_processed_player_df["role_BAT"] * selection_decision_variables_df["pulp_variable"])
    prob += (total_batsmen >= 3)
    prob += (total_batsmen <= 6)

    # 1 <= n_allrounders <= 4
    total_allrounders = pulp.lpSum(merged_processed_player_df["role_AR"] * selection_decision_variables_df["pulp_variable"])
    prob += (total_allrounders >= 1)
    prob += (total_allrounders <= 4)

    # 3 <= n_bowlers <= 6
    total_bowlers = pulp.lpSum(merged_processed_player_df["role_BWL"] * selection_decision_variables_df["pulp_variable"])
    prob += (total_bowlers >= 3)
    prob += (total_bowlers <= 6)

    # maximum of 11 players
    total_players = pulp.lpSum(selection_decision_variables_df["pulp_variable"])
    prob += (total_players == 11)

    # maximum fantasy budget of 100
    total_cost = pulp.lpSum(merged_processed_player_df["credit"] * selection_decision_variables_df["pulp_variable"])
    prob += (total_cost <= 100)

    # we cannot pick more than 7 players from the same team
    team_name_lp1 = "team_" + team1_name
    team_name_lp2 = "team_" + team2_name
    total_team1 = pulp.lpSum(merged_processed_player_df[team_name_lp1] * selection_decision_variables_df["pulp_variable"])
    prob += (total_team1 <= 7)

    total_team2 = pulp.lpSum(merged_processed_player_df[team_name_lp2] * selection_decision_variables_df["pulp_variable"])
    prob += (total_team2 <= 7)

    print(prob)
    prob.writeLP('Dreamteam.lp')

    assert len(pulp.listSolvers(onlyAvailable=True)) > 0, "solvers not installed correctly - check - https://www.coin-or.org/PuLP/main/installing_pulp_at_home.html"
    prob.solve()

    # prep solution

    solutions_df = pd.DataFrame(
        [
            {
                'pulp_variable_name': v.name, 
                'value': v.varValue
            }
            for v in prob.variables()
        ]
    )


    result = pd.merge(merged_processed_player_df, solutions_df, on = 'pulp_variable_name')
    result = result[result['value'] == 1].sort_values(by = 'points', ascending = False)
    print(result)
    role_df = undummify(result[['role_AR','role_BAT','role_BWL','role_WK']])
    print(role_df)
    result['role'] = role_df['role']

    teamname_df = undummify(result[[ team_name_lp1, team_name_lp2]])
    result['team'] = teamname_df['team']
    print(result)
    print('after',result.shape)
    selected_cols_final = ['player', 'team','points', 'credit','role']
    final_set_of_players_to_be_selected = result[selected_cols_final]
    final_set_of_players_to_be_selected.reset_index(drop=True, inplace=True)
    print(final_set_of_players_to_be_selected)

    print("We can accrue an estimated points of %f"%(final_set_of_players_to_be_selected['points'].sum()))
    print("We want to see credits utilised %f"%(final_set_of_players_to_be_selected['credit'].sum()) )

    final_set_of_players_to_be_selected.to_json('ft.json')

    return final_set_of_players_to_be_selected


if __name__ == "__main__":
    app.run(debug=True)