# pip3 install trueskill
# Docs: http://trueskill.org/

import csv
from trueskill import Rating, TrueSkill, rate_1vs1, BETA
from math import sqrt
from trueskill.backends import cdf

def win_probability(rating_a, rating_b):
    delta_mu = rating_a.mu - rating_b.mu
    denom = sqrt(2 * (BETA * BETA) + pow(rating_a.sigma, 2) \
                 + pow(rating_b.sigma, 2))
    return cdf(delta_mu / denom)

# Get matches to predict
predict_titles = []
matches_to_predict = []
with open('dataset/SampleSubmission.csv', newline = '') as csvfile:
    reader = csv.reader(csvfile, delimiter = ',')
    predict_titles.append(reader.__next__())
    for row in reader:
        matches_to_predict.append(row[0])

# Get regular season match results
regular_res_titles = []
regular_res = []
with open('dataset/RegularSeasonCompactResults.csv', newline = '') as csvfile:
    reader = csv.reader(csvfile, delimiter = ',')
    regular_res_titles = reader.__next__()
    for row in reader:
        if int(row[regular_res_titles.index('Season')]) >= 2008:
            regular_res.append(row)

# Get all teams           
teams = matches_to_predict[0].split('_')[1:]
for recd in matches_to_predict[1:]:
    ret = recd.split('_')
    if ret[1] == teams[0]:
        teams.append(ret[2])
    else:
        break

# Calculate the probability of draw given different score differences
draw_rates = dict()
for score_diff in range(0, 11):
    num_draw = 0
    for recd in regular_res:
        if int(recd[regular_res_titles.index('Wscore')]) - \
           int(recd[regular_res_titles.index('Lscore')]) <= score_diff:
            num_draw = num_draw + 1
    draw_rates[score_diff] = num_draw / len(regular_res)

# Build models for all score differences
for score_diff in draw_rates.keys():
    env = TrueSkill(draw_probability = draw_rates[score_diff])
    team_rating = dict(zip(teams, [env.create_rating()] * len(teams)))
    for recd in regular_res:
        wteam = recd[regular_res_titles.index('Wteam')]
        lteam = recd[regular_res_titles.index('Lteam')]
        wscore = int(recd[regular_res_titles.index('Wscore')])
        lscore = int(recd[regular_res_titles.index('Lscore')])

        if wteam in team_rating and lteam in team_rating:
            team_rating[wteam], team_rating[lteam] = rate_1vs1(team_rating[wteam],\
                team_rating[lteam], drawn = (wscore - lscore <= score_diff), env = env)
     
    probabilities = []
    for i in range(0, len(teams)):
        for j in range(i + 1, len(teams)):
            probabilities.append(win_probability(team_rating[teams[i]], team_rating[teams[j]]))

    predict_res = list(zip(matches_to_predict, probabilities))
    with open('dataset/results/predict' + str(score_diff) + '.csv', 'w', newline = '') as csvfile:
        writer = csv.writer(csvfile, quoting = csv.QUOTE_MINIMAL)
        writer.writerows(predict_titles)
        writer.writerows(predict_res)
