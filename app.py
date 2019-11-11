import json

import numpy as np
import pandas as pd

# Use k-dimensional tree to get hitorical shot information
# related to a nearest shot location
import kdtree

from flask import Flask, jsonify, render_template, request, make_response
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy

from sklearn.externals import joblib

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


# For manual Standard-Scaling for the user-inputted shot locations
with open('static/db/scaler_statisics.json', 'r') as stats:
    stats_json = json.load(stats)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shotchart/<player_id>", methods=['GET'])
def get_shotchart_for_player(player_id):
    # Get player's shot chart data for all season except for 2019-20
    query = f"""
        SELECT *
         FROM shotcharts sc
         WHERE sc.PLAYER_ID = {player_id}
         AND sc.GAME_DATE NOT LIKE '2019%'
    """
    df = pd.read_sql(query, con=db.session.bind)
    json = eval(df[['LOC_X', 'LOC_Y', 'EVENT_TYPE']].to_json(
        orient='table', index=False))['data']
    return jsonify(json)


# Getting the user inputs from front-end using js fetch API and Flask request
@app.route("/user-input", methods=["POST"])
def post_user_inputs():

    req = request.get_json()
    print(req)

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
            x - stats_json[player_name]['mean_x']) / stats_json[player_name]['std_x'])
        df['scaled_LOC_Y'] = df['LOC_Y'].map(lambda y: (
            y - stats_json[player_name]['mean_y']) / stats_json[player_name]['std_y'])
        df['angle'] = df['scaled_LOC_X'] / df['scaled_LOC_Y']
        df = df.drop(columns=['original_x', 'original_y',
                              'scaled_LOC_X', 'scaled_LOC_Y', 'LOC_X', 'LOC_Y'])

        return (player_name, df)

    def generate_X_test(player_name, df):
        # Generate a test dataset for the prediction based on user-input
        df_encoded = pd.get_dummies(df)
        user_features = set(df_encoded.columns)
        player_features = set(pd.read_pickle(
            f'static/models/step1/features/{player_name}_features').iloc[:, 1].to_list())
        feature_differences = player_features - user_features
        fake_df = pd.DataFrame(
            np.zeros((len(df), len(feature_differences)), dtype='int64'), columns=feature_differences)

        X_test = df_encoded.join(fake_df)

        return X_test

    player_name, df_user_shots = generate_shot_info(req)
    X_test = generate_X_test(player_name, df_user_shots)
    # print(f"The Shape of X_test (outside function): {X_test.shape}")

    # * Invoke a player's trained model (RandomForest) and make a prediction
    # * using joblib
    model = joblib.load(f'static/models/step1/{player_name}')
    y_predict_step1 = model.predict(X_test)
    # print(y_predict_step1)

    FG_PCT = y_predict_step1[X_test['SHOT_TYPE_2PT Field Goal'] == 1].sum(
    ) / len(y_predict_step1)
    FG3_PCT = y_predict_step1[X_test['SHOT_TYPE_3PT Field Goal'] == 1].sum(
    ) / len(y_predict_step1)

    print(f'FG%= {FG_PCT}, FG3%= {FG3_PCT}')

    res = make_response(jsonify({"message": "OK"}), 200)

    return res


if __name__ == "__main__":
    app.run(debug=True)
