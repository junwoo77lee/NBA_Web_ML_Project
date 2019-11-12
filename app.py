import warnings
from sklearn.externals import joblib
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask import Flask, jsonify, render_template, request, make_response

# Use k-dimensional tree to get hitorical shot information
# related to a nearest shot location
import kdtree
import pandas as pd
import numpy as np
import json
from nba_api.stats.endpoints import LeagueDashPlayerStats

# NBA_API requires this headers to correctly get a dataset when XHR
headers = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36',
    'Sec-Fetch-User': '?1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/leaguedashplayerstats.md',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

# force to avoid any warnings, especially the ones from sklearn which are not importants


def warn(*args, **kwargs):
    pass


warnings.warn = warn


# Create an app
app = Flask(__name__)

# Set-up Databases
db_name = 'shotcharts.db'
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///static/db/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# To generate general information for each shot location defined by user
class Shot:
    #
    def __init__(self, original_x, original_y, action_type, shot_type, shot_zone_basic, shot_zone_area, shot_zone_range, shot_distance):
        self.original_x = original_x
        self.original_y = original_y
        self.ACTION_TYPE = action_type
        self.SHOT_TYPE = shot_type
        self.SHOT_ZONE_BASIC = shot_zone_basic
        self.SHOT_ZONE_AREA = shot_zone_area
        self.SHOT_ZONE_RANGE = shot_zone_range
        self.SHOT_DISTANCE = shot_distance


# For generating ACTION_TYPE_DICT to form a KDtree (2019 excluded)
def shotchart_for_all_players():
    query = f'''
            SELECT ACTION_TYPE, SHOT_TYPE, SHOT_ZONE_BASIC, SHOT_ZONE_AREA,
                   SHOT_ZONE_RANGE, SHOT_DISTANCE, LOC_X, LOC_Y
             FROM shotcharts sc
             WHERE sc.GAME_DATE NOT LIKE "2019%"
             '''
    df = pd.read_sql(query, con=db.session.bind)
    return df


def shotchart_for_all_players_excluding_duplicate_shot_locations():
    query = f'''
            SELECT *
             FROM
                 (SELECT *,
                         ROW_NUMBER() OVER (PARTITION BY X_Y ORDER BY X_Y)  AS X_Y_ordered
                   FROM (SELECT *, LOC_X || "_" || LOC_Y AS X_Y
                          FROM shotcharts sc
                          WHERE sc.GAME_DATE NOT LIKE "2019%")
                 )
             WHERE X_Y_ordered = 1
             '''
    df = pd.read_sql(query, con=db.session.bind)
    return df


# Create a dictionary which contains the most common action type for each historical shot location
df_all_players = shotchart_for_all_players()
df_all_players_action_type = df_all_players.groupby(['LOC_X', 'LOC_Y']).agg(
    {'ACTION_TYPE': lambda x: pd.Series.mode(x)[0]}).reset_index()
df_all_players_action_type = df_all_players_action_type[['LOC_X', 'LOC_Y', 'ACTION_TYPE']].set_index([
    'LOC_X', 'LOC_Y'])
ACTION_TYPE_DICT = df_all_players_action_type.to_dict()['ACTION_TYPE']

df_all_players_unique_shots = shotchart_for_all_players_excluding_duplicate_shot_locations()

# load the historical shot-chart data
_shot_chart_kdtree = kdtree.create(dimensions=2)
SHOT_CHART_DICT = {}

# populate shot locations into kdtree
for shot in df_all_players_unique_shots.itertuples():
    shot_location_key = (int(shot[18]), int(shot[19]))
    _shot_chart_kdtree.add(shot_location_key)
    action_type = ACTION_TYPE_DICT[shot_location_key]
    c = Shot(shot[18], shot[19], action_type, shot[13],
             shot[14], shot[15], shot[16], shot[17])
    SHOT_CHART_DICT[shot_location_key] = c


# find nearest shot location
def nearest_shot(loc_x, loc_y):
    nearest_shot_location = _shot_chart_kdtree.search_nn((loc_x, loc_y, ))
    return SHOT_CHART_DICT[nearest_shot_location[0].data]


# For manual Standard-Scaling for Step1
with open('static/db/step1_scaler_statistics.json', 'r') as stats_step1:
    stats_json_step1 = json.load(stats_step1)

# For manual Standard-Scaling for Step3
with open('static/db/step3_scaler_statistics.json', 'r') as stats_step3:
    stats_json_step3 = json.load(stats_step3)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/players-2018-stats", methods=['GET'])
def get_player_stats():

    # todo: make a endpoint to grap player's stats to display on the browser
    pass

    return


@app.route("/shotchart", methods=['GET'])
def get_shotchart_for_player():

    # FLASK request.args to use query params
    # Alternative to the path param: '/shotchart/<player_id>/<where>'
    player_id = request.args.get('playerId')
    where = request.args.get('where')

    # Get player's shot chart data for all season except for 2019-20
    query = f"""
        SELECT *
         FROM shotcharts sc
         WHERE sc.PLAYER_ID = {player_id}
         AND sc.GAME_DATE {where} '2019%'
    """
    df = pd.read_sql(query, con=db.session.bind)
    json = eval(df[['LOC_X', 'LOC_Y', 'SHOT_ATTEMPTED_FLAG']].to_json(
        orient='table', index=False))['data']
    return jsonify(json)


# Getting the user inputs from front-end using js fetch API and Flask request
@app.route("/user-input", methods=["POST"])
def post_user_inputs():
    # Getting data posted by the front-end
    req = request.get_json()
    print(req)

    # player_id = req['playerId'].strip()
    player_name_for_stat = req['playerName'].strip()
    if player_name_for_stat == "Lebron James":
        player_name_for_stat = "LeBron James"

    # Get player's stats for the current season (2019-20)
    df_lps = LeagueDashPlayerStats(
        league_id_nullable='00', headers=headers).league_dash_player_stats.get_data_frame().set_index('PLAYER_NAME')

    #########################################################################
    #
    # STEP1 Prediction: predict shot-made% based on shot location information
    #
    #########################################################################

    FG_PCT_2019 = df_lps.loc[player_name_for_stat]['FG_PCT']
    FG3_PCT_2019 = df_lps.loc[player_name_for_stat]['FG3_PCT']
    print(f"FG%_2019={FG_PCT_2019}, FG3%_2019={FG3_PCT_2019}")

    # EXAMPLE of req:
    # {'playerName': ' Al Horford ',
    #  'data': [{'LOC_X': 96, 'LOC_Y': 160, 'SHOT_ATTEMPTED_FLAG': 1}, {'LOC_X': 31, 'LOC_Y': 160, 'SHOT_ATTEMPTED_FLAG': 1}, {'LOC_X': -31, 'LOC_Y': 160, 'SHOT_ATTEMPTED_FLAG': 1}]}

    def generate_shot_info(user_json):
        # generate a dataframe which contains shot information matched to the user-inputs
        df = pd.DataFrame(user_json['data'])
        df_shot_information = pd.DataFrame(
            list(map(vars, (map(nearest_shot, df['LOC_X'], df['LOC_Y'])))))
        df = df.join(df_shot_information)

        # Calculate "angle" feature after scaling 'LOC_X' and 'LOC_Y' based on the distribution
        #  from the standardScaler during training
        player_name = user_json['playerName'].strip()
        df['scaled_LOC_X'] = df['LOC_X'].map(lambda x: (
            x - stats_json_step1[player_name]['mean_x']) / stats_json_step1[player_name]['std_x'])
        df['scaled_LOC_Y'] = df['LOC_Y'].map(lambda y: (
            y - stats_json_step1[player_name]['mean_y']) / stats_json_step1[player_name]['std_y'])
        df['angle'] = df['scaled_LOC_X'] / df['scaled_LOC_Y']
        df = df.drop(columns=['original_x', 'original_y',
                              'scaled_LOC_X', 'scaled_LOC_Y', 'LOC_X', 'LOC_Y'])

        return (player_name, df)

    def generate_X_test(player_name, df):
        # Generate a test dataset for the prediction based on user-input
        df_encoded = pd.get_dummies(df)
        user_features = set(df_encoded.columns)
        print(f'U = {len(user_features)}')
        player_features = set(pd.read_pickle(
            f'static/models/step1/features/{player_name}_features').iloc[:, 1].to_list())
        print(f'P = {len(player_features)}')
        feature_differences = player_features - user_features
        print(f'P - U = {len(player_features - user_features)}')
        print(f'U - P = {len(user_features - player_features)}')

        should_be_zero = len(user_features - player_features)

        fake_df = pd.DataFrame(
            np.zeros((len(df), len(feature_differences) - should_be_zero), dtype='int64'), columns=list(feature_differences)[should_be_zero:])

        X_test = df_encoded.join(fake_df)

        return X_test

    player_name, df_user_shots = generate_shot_info(req)
    X_test_step1 = generate_X_test(player_name, df_user_shots)

    # * Invoke a player's trained model (RandomForest) and make a prediction
    # * using joblib
    model_step1 = joblib.load(f'static/models/step1/{player_name}')
    y_predict_step1 = model_step1.predict(X_test_step1)
    # print(y_predict_step1)

    FG_PCT_predicted = y_predict_step1[X_test_step1['SHOT_TYPE_2PT Field Goal'] == 1].sum(
    ) / len(y_predict_step1)
    FG3_PCT_predicted = y_predict_step1[X_test_step1['SHOT_TYPE_3PT Field Goal'] == 1].sum(
    ) / len(y_predict_step1)

    print("Prediction results from STEP1:")
    print(f'FG%= {FG_PCT_predicted}, FG3%= {FG3_PCT_predicted}')

    #########################################################################
    #
    # STEP2 Prediction: predict player's score based on shot-made%
    #
    #########################################################################

    # total number of games, player's points, and play time for the current season
    # (time in minutes)
    number_of_games = df_lps.loc[player_name_for_stat]['GP']
    total_pts = df_lps.loc[player_name_for_stat]['PTS']
    total_playing_time = df_lps.loc[player_name_for_stat]['MIN']

    PTS_player_AVG_2019 = total_pts / number_of_games

    # feature addtion: playing time% per a game
    # divided by the maximum minutes per a game in the dataset
    PLAYING_PCT = (total_playing_time /
                   number_of_games) / 60

    # todo: apply the scaler's distribution for each feature
    model_step2 = joblib.load(f'static/models/step2/{player_name}')

    scaled_FG_PCT = FG_PCT_predicted
    scaled_FG3_PCT = FG3_PCT_predicted
    scaled_PLAYING_PCT = PLAYING_PCT

    X_test_step2 = {'FG_PCT': scaled_FG_PCT,
                    'FG3_PCT': scaled_FG3_PCT,
                    'PLAYING%': scaled_PLAYING_PCT}

    X_test_step2 = pd.DataFrame(X_test_step2, index=[0])
    PTS_player_predicted = model_step2.predict(X_test_step2)[0]

    print("Prediction results from STEP2:")
    print(f"Predicted Player's Score = {PTS_player_predicted}")

    #########################################################################
    #
    # STEP3 Prediction: predict team's score based on player's score
    #
    #########################################################################

    model_step3 = joblib.load(f'static/models/step3/{player_name}')

    # Get a player's average PLUS_MINUS points for the current season (2019-20)
    player_PM = df_lps.loc[player_name_for_stat]['PLUS_MINUS'] / \
        df_lps.loc[player_name_for_stat]['GP']

    # todo: apply the scaler's distribution for each feature
    scaled_PTS_player = (PTS_player_predicted - stats_json_step3[player_name]
                         ['mean_PLAYER_PTS']) / stats_json_step3[player_name]['std_PLAYER_PTS']
    scaled_player_PM = (
        player_PM - stats_json_step3[player_name]['mean_PLUS_MINUS']) / stats_json_step3[player_name]['std_PLUS_MINUS']

    X_test_step3 = {'PLAYER_PTS': scaled_PTS_player,
                    'PLUS_MINUS': scaled_player_PM
                    }
    X_test_step3 = pd.DataFrame(X_test_step3, index=[0])
    PTS_team_predicted = model_step3.predict(X_test_step3)[0]

    print("Prediction results from STEP3:")
    print(f"Predicted Team's Score = {PTS_team_predicted}")

    #########################################################################
    #
    # STEP4 Prediction: predict Win/Lose result based on team's score
    #
    #########################################################################

    # todo: apply the scaler's distribution for each feature

    # model_step3 = joblib.load(f'static/models/step4/{player_name}')

    res = [{
        'FG_PCT': FG_PCT_predicted,
        'FG3_PCT': FG3_PCT_predicted,
        'FG_PCT_2019': FG_PCT_2019,
        'FG3_PCT_2019': FG3_PCT_2019,
        'PTS_player': PTS_player_predicted,
        'PTS_player_AVG_2019': PTS_player_AVG_2019
    }]

    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=True)
