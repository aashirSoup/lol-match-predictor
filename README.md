# League of Legends Match Predictor

A machine learning project that predicts the outcome of League of Legends matches based on champion picks, team composition, and player data.

> **This project is currently under development.**

## About

This app uses match data from Riot Games' API to train a model that can predict which team is more likely to win a given game. Users will be able to select 10 champions and get a win probability for each side.

## How It Works

1. **Data Collection** — Match data is pulled from the Riot Games API (Diamond+ ranked games)
2. **Feature Engineering** — Raw match data is transformed into useful inputs like team composition breakdown, champion synergies, and player rank
3. **Model Training** — An XGBoost model is trained on the processed data to learn patterns that lead to wins and losses
4. **Prediction** — Given a set of 10 champion picks, the model outputs a win probability for each team

## Tech Stack

- **Data & ML:** Python, pandas, scikit-learn, XGBoost
- **Backend:** FastAPI
- **Frontend:** Streamlit or React (TBD)
- **Data Source:** Riot Games API

## Project Status

- [ ] Data collection pipeline
- [ ] Data cleaning & feature engineering
- [ ] Exploratory data analysis
- [ ] Baseline model (Logistic Regression)
- [ ] Tuned models (Random Forest, XGBoost)
- [ ] Backend API
- [ ] Frontend interface
- [ ] Deployment

## Running Locally

_Instructions will be added once the project is ready to run._

## Acknowledgments

- Match data provided by the [Riot Games API](https://developer.riotgames.com/)
- This project isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties
