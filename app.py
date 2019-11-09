import pandas as pd

from flask import Flask, jsonify, render_template, request, make_response
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy

# Create an app
app = Flask(__name__)

# Set-up Databases
db_name = 'shotcharts.db'
app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///static/db/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/shotchart/<player_id>", methods=['GET'])
def get_shotchart_for_player(player_id):
    query = f"""
        SELECT *
         FROM shotcharts sc
         WHERE sc.PLAYER_ID = {player_id}
         AND sc.GAME_DATE LIKE '2019%'
    """
    df = pd.read_sql(query, con=db.session.bind)
    json = eval(df[['LOC_X', 'LOC_Y', 'EVENT_TYPE']].to_json(
        orient='table', index=False))['data']
    return jsonify(json)


# @app.route('/api', methods=['POST'])
# def api():
#     # Do something useful here...
#     return request.values.get('input', '')


@app.route("/shochart/user-input", methods=["POST"])
def post_user_inputs():

    req = request.get_json()

    print(req)

    res = make_response(jsonify({"message": "OK"}), 200)

    return res


if __name__ == "__main__":
    app.run(debug=True)
