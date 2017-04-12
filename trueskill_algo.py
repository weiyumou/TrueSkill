# pip3 install trueskill
# Docs: http://trueskill.org/
import math
import trueskill
import csv
from copy import deepcopy

# import matplotlib.pyplot as plt
# import numpy as np
# import matplotlib.mlab as mlab
# import matplotlib.pylab as plb


class NaiveEvaluator:
    def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj):
        self.teams = eval_teams
        self.regular_titles = regu_titles
        self.regular_matches = regu_matches
        self.victory_margin = vic_margin
        self.lower_adj = l_adj
        self.upper_adj = u_adj
        # self.rating_history = {eval_teams[0]: [], eval_teams[1]: []}

    def rate_team(self):
        trueskill.setup(draw_probability=self.draw_prob())
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

                # self.rating_history[wteam].append(team_rating[wteam])
                # self.rating_history[lteam].append(team_rating[lteam])
                team_rating[wteam], team_rating[lteam] = trueskill.rate_1vs1(team_rating[wteam],
                                                                             team_rating[lteam],
                                                                             drawn=self.is_equal_score(wscore, lscore))
                wscore -= self.victory_margin

                while wscore - lscore >= self.victory_margin:
                    # self.rating_history[wteam].append(team_rating[wteam])
                    # self.rating_history[lteam].append(team_rating[lteam])
                    team_rating[wteam], team_rating[lteam] = trueskill.rate_1vs1(team_rating[wteam],
                                                                                 team_rating[lteam],
                                                                                 drawn=self.is_equal_score(wscore,
                                                                                                           lscore))
                    wscore -= self.victory_margin
        return team_rating

    def predict(self, team_rating):
        probabilities = []
        for i in range(0, len(teams)):
            for j in range(i + 1, len(teams)):
                prob = self.win_probability(team_rating[teams[i]], team_rating[teams[j]])
                # if prob <= self.lower_adj:
                #     prob = 0.0
                # elif prob >= self.upper_adj:
                #     prob = 1.0
                probabilities.append(prob)
        return probabilities

    def start_evaluation(self):
        team_rating = self.rate_team()
        return self.predict(team_rating)

    def draw_prob(self):
        num_draw = 0
        for match in self.regular_matches:
            wscore = match[self.regular_titles.index('Wscore')]
            lscore = match[self.regular_titles.index('Lscore')]
            if self.is_equal_score(wscore, lscore):
                num_draw += 1
        return num_draw / len(self.regular_matches)

    @staticmethod
    def is_equal_score(wscore, lscore):
        return abs(wscore - lscore) <= 1e-7

    @staticmethod
    def win_probability(rating_a, rating_b):
        delta_mu = rating_a.mu - rating_b.mu
        denom = math.sqrt(2 * (trueskill.BETA * trueskill.BETA) + pow(rating_a.sigma, 2) \
                          + pow(rating_b.sigma, 2))
        return trueskill.backends.cdf(delta_mu / denom)


class HomeCourtAdv(NaiveEvaluator):
    def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg):
        super().__init__(eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj)
        self.home_adv = home_advtg

    def home_adv_adjust(self):
        for match in self.regular_matches:
            wloc = match[self.regular_titles.index('Wloc')]
            if wloc == 'H':
                match[self.regular_titles.index('Wscore')] -= self.home_adv

    def start_evaluation(self):
        self.home_adv_adjust()
        return super().start_evaluation()


class OvertimeAsDraw(HomeCourtAdv):
    def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg):
        super().__init__(eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg)

    def adjust_overtime(self):
        for match in self.regular_matches:
            numot = match[self.regular_titles.index('Numot')]
            if numot > 0:
                match[self.regular_titles.index('Wscore')] = match[self.regular_titles.index('Lscore')]

    def start_evaluation(self):
        self.adjust_overtime()
        return super().start_evaluation()


start_season = 2005
end_season = 2016  # inclusive

# Get matches to predict
predict_titles = []
predict_matches = []
with open('dataset/SampleSubmission.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    predict_titles.append(reader.__next__())
    for row in reader:
        predict_matches.append(row[0])

# Get regular season match results
regular_titles = []
regular_matches = []
with open('dataset/RegularSeasonCompactResults.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
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

# teams = ['1211', '1365']

# Home advantage: deduct x scores from a home-winner
max_home_adv = 2.0
victory_margin = math.inf
max_lower_adj = 0.11
min_upper_adj = 0.89

home_adv = 1.5
while home_adv < max_home_adv:
    lower_adj = 0.1
    while lower_adj < max_lower_adj:
        upper_adj = 0.9
        while upper_adj > min_upper_adj:
            # use default value for victory_margin to disable this feature
            evaluator = HomeCourtAdv(teams, regular_titles, deepcopy(regular_matches),
                                       victory_margin, lower_adj, upper_adj, home_adv)
            probs = evaluator.start_evaluation()
            predict_res = list(zip(predict_matches, probs))
            with open('results/{0}_{1}_{2}.csv'.format(str(home_adv).replace('.', '_'), str(lower_adj).replace('.', '_'),
                                                      str(upper_adj).replace('.', '_')), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(predict_titles)
                writer.writerows(predict_res)
            upper_adj -= 0.01
        lower_adj += 0.01
    home_adv += 0.5
    # row = 0
    # while row < len(ratings['1211']):
    #     mu1 = ratings['1211'][row].mu
    #     sigma1 = ratings['1211'][row].sigma
    #     x1 = np.linspace(mu1 - 3 * sigma1, mu1 + 3 * sigma1)
    #
    #     mu2 = ratings['1365'][row].mu
    #     sigma2 = ratings['1365'][row].sigma
    #     x2 = np.linspace(mu2 - 3 * sigma2, mu2 + 3 * sigma2)
    #     plb.ylim([0, 0.25])
    #     plt.plot(x1, mlab.normpdf(x1, mu1, sigma1), x2, mlab.normpdf(x2, mu2, sigma2))
    #     plb.savefig('figures/' + str(row) + '.png')
    #     plt.gcf().clear()
    #     row += 1



