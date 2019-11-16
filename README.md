# NBA Machine Learning Project

### Objective

To build a user interactive website that allows for the selection of the 2018 Top NBA players according to https://www.si.com/nba/2017/09/14/nba-top-100-players-2018-lebron-james-stephen-curry-kevin-durant.  Once players are selected the objective was to run user selected or randomly generated shot locations to predict various NBA player/team results.

### Purpose/Goal

The project attempted to determine the best Machine Learning models for each player.  Once the player module was identified, the trained model is applied to generate results based on user interactions with the Flask website.  From the predicated  a comparison is created to display the models performance and current 2019 player statistics. 

#### Step 1: Predict Player 2pt/3pt shots

This step looked at individual player's field goals made and their field goals attempted. The players career statistical data is from the nba.stats python library.  Each of the player's stats were tested in 4 ML models, the best performing module was chosen to predict the percentage of 2pts shots and 3pts.  The predicted model is compared to the players actual 2019-20 game data accessed in early November, 2019.

#### Step 2: Predict the Players Total Game Score 

Based on the module from step 1, using a similar process of running individual player data through 4 ML models, the best model is selected to predict the players overall score.  The overall score is then compared to the player 2019-20 average pts per game.

#### Step 3: Predict the Team's score

The project assumption is that the team’s best players performance would allow for the prediction of the teams total score for a simulated game.  Based on step two data, 4 ML models are executed to determine the teams overall score based on the predict players score.  The predicted value is compared with the team’s 2019-20 average total score.

#### Step 4: Win or Lose

Finally, based on the teams predicted score, the model is then trained to calculate if the team would win or lose.  Since each step described above is dependent on the next, the model is basing the win or loss data off of the predict players shooting results.   The outcome is ran through 4 ML models, and the most accurate model is selected.   

### Conclusion

The results were a bit limited based on the limited interaction type provided by the website which restricted the amount of features included in the initial player's field goal percentage.  Features such as shot type, free throw, layup, etc. may have helped create stronger more accurate Machine Learning Models.

### Technologies Used

- Python
- Jupyter Notebook
- SQLite
- HTML5/ CSS3/ Bootstrap4
- JavaScript


#### Modules Used

- Pandas
- Numpy
- Flask
- SQLAlchemy
- Scikit Learn
- NBA_api
- MatplotLib
- Seaborn
- d3.js
- jquery


#### Machine Learning techniques Used

- SVM
- Decision Tree Regressor
- Random Forest Regressor
- Voting Regressor/ Classifier
- Logistic Regression
- MLP (Neural Networks)


### To Run

Required to run in scikit-learn 0.21.2 or 0.21.3

After cloning the project, the large files below should be download into models/step1

Step 1 Files - https://www.dropbox.com/sh/zyqt6z0l3kpixrv/AADV2zMfCaiS832AjVMGTZFka?dl=0

Similiar to above, the files below should be downladed into models/step4

Step 4 Files - https://www.dropbox.com/sh/uobmx2ysvwqie2u/AAAFeMvouLDY6TpB7Er-zmOZa?dl=0
