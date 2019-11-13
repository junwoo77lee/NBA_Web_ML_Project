# NBA Machine Learning Project

### Objective

To build a user interactive website that allows for the selection of the 2018 Top NBA players according to https://www.si.com/nba/2017/09/14/nba-top-100-players-2018-lebron-james-stephen-curry-kevin-durant.  Once players are selected the objective was to run user selected or randomly generated shot locations to predict various NBA results.

### Purpose/Goal

The project attempted to determine the best Machine Learning modules for each player.  Once the player module was identified, the trained model is applied to generate resultes based on user interactions with the Flask website.  From the predicited models a comparison is created to display the modules performance and current 2019 player statistics. 

#### Step 1: Predict Player 2pt/3pt shots

This step looked at players field goals made, field goals attempted from the players career statistics using the nba.stats python library.  Each player's stats were tested in 4 ML modules, the best peforming module was chosen to   
