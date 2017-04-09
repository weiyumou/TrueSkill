# pip3 install trueskill
# Docs: http://trueskill.org/
import math
import trueskill
class NaiveEvaluator:
    def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin = math.inf):
        self.teams = eval_teams
        self.regular_titles = regu_titles
        self.regular_matches = regu_matches
        self.victory_margin = vic_margin
##        self.leaderboard = None
        
    def rate_team(self):
        trueskill.setup(draw_probability = self.draw_prob())
        team_rating = dict(zip(self.teams, [trueskill.global_env().create_rating()] * len(self.teams)))
        for match in self.regular_matches:
            wteam = match[self.regular_titles.index('Wteam')]
            lteam = match[self.regular_titles.index('Lteam')]
            wscore = match[self.regular_titles.index('Wscore')]
            lscore = match[self.regular_titles.index('Lscore')]

            if wteam in team_rating and lteam in team_rating:
                if wscore < lscore:
                    wteam, lteam = lteam, wteam
                    wscore, lscore = lscore, wscore
                    
                team_rating[wteam], team_rating[lteam] = trueskill.rate_1vs1(team_rating[wteam], \
                    team_rating[lteam], drawn = self.is_equal_score(wscore, lscore))
                wscore -= self.victory_margin
                
                while wscore - lscore >= self.victory_margin:
                    team_rating[wteam], team_rating[lteam] = trueskill.rate_1vs1(team_rating[wteam], \
                        team_rating[lteam], drawn = self.is_equal_score(wscore, lscore))
                    wscore -= self.victory_margin

##        leaderboard = sorted(list(team_rating.values()), key = trueskill.expose, reverse = True)
##        print(leaderboard)
        return team_rating

    def predict(self, team_rating):
        probs = []
        for i in range(0, len(teams)):
            for j in range(i + 1, len(teams)):
                prob = self.win_probability(team_rating[teams[i]], team_rating[teams[j]])
                probs.append(prob)
        return probs

    def startEvaluation(self):
        team_rating = self.rate_team()                              
        return self.predict(team_rating)

    def is_equal_score(self, wscore, lscore):
        return abs(wscore - lscore) <= 1e-7

    def draw_prob(self):
        num_draw = 0
        for match in self.regular_matches:
            wscore = match[self.regular_titles.index('Wscore')]
            lscore = match[self.regular_titles.index('Lscore')]
            if self.is_equal_score(wscore, lscore):
                num_draw += 1
        return num_draw / len(self.regular_matches)

    def win_probability(self, rating_a, rating_b):
        delta_mu = rating_a.mu - rating_b.mu
        denom = math.sqrt(2 * (trueskill.BETA * trueskill.BETA) + pow(rating_a.sigma, 2) \
                     + pow(rating_b.sigma, 2))
        return trueskill.backends.cdf(delta_mu / denom)

class HomeCourtAdv(NaiveEvaluator):
    def __init__(self, eval_teams, regu_titles, regu_matches, home_advtg, vic_margin):
        super().__init__(eval_teams, regu_titles, regu_matches, vic_margin)
        self.home_adv = home_advtg

    def home_adv_adjust(self):
        for match in self.regular_matches:
            wloc = match[self.regular_titles.index('Wloc')]
            if wloc == 'H':
                match[self.regular_titles.index('Wscore')] -= self.home_adv
    def startEvaluation(self):
        self.home_adv_adjust()
        return super().startEvaluation()
    
class NoOvertime(HomeCourtAdv):
    def __init__(self, eval_teams, regu_titles, regu_matches, home_advtg, vic_margin):
        super().__init__(eval_teams, regu_titles, regu_matches, home_advtg, vic_margin)
        
    def adjust_overtime(self):
        for match in self.regular_matches:
            numot = match[self.regular_titles.index('Numot')]
            if numot > 0:
                match[self.regular_titles.index('Wscore')] = match[self.regular_titles.index('Lscore')]

    def startEvaluation(self):
        self.adjust_overtime()
        return super().startEvaluation()      

import csv
start_season = 2005
end_season = 2016 #inclusive

# Get matches to predict
predict_titles = []
predict_matches = []
with open('dataset/SampleSubmission.csv', newline = '') as csvfile:
    reader = csv.reader(csvfile, delimiter = ',')
    predict_titles.append(reader.__next__())
    for row in reader:
        predict_matches.append(row[0])

# Get regular season match results
regular_titles = []
regular_matches = []
with open('dataset/RegularSeasonCompactResults.csv', newline = '') as csvfile:
    reader = csv.reader(csvfile, delimiter = ',')
    regular_titles = reader.__next__()
    for row in reader:
        row[regular_titles.index('Season')] = int(row[regular_titles.index('Season')])
        season = row[regular_titles.index('Season')]
        if start_season <= season <= end_season:
            row[regular_titles.index('Wscore')] = float(row[regular_titles.index('Wscore')])
            row[regular_titles.index('Lscore')] = float(row[regular_titles.index('Lscore')])
            row[regular_titles.index('Numot')] = int(row[regular_titles.index('Numot')])
            regular_matches.append(row)

# Get all teams
teams = predict_matches[0].split('_')[1:]
for recd in predict_matches[1:]:
    ret = recd.split('_')
    if ret[1] == teams[0]:
        teams.append(ret[2])
    else:
        break

from copy import deepcopy
# Home advantage: deduct x scores from a home-winner
max_home_adv = 2
home_adv = 1.5
victory_margin = 11
while home_adv < max_home_adv:
    # use default value for victory_margin to disable this feature
    evaluator = NoOvertime(teams, regular_titles, deepcopy(regular_matches), home_adv, victory_margin)
    probs = evaluator.startEvaluation()
    predict_res = list(zip(predict_matches, probs))
    with open('results/' + str(home_adv).replace('.', '_') + '.csv', 'w', newline = '') as csvfile:
        writer = csv.writer(csvfile, quoting = csv.QUOTE_MINIMAL)
        writer.writerows(predict_titles)
        writer.writerows(predict_res)
    home_adv += 0.5
