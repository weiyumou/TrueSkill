# pip3 install trueskill
# Docs: http://trueskill.org/

class TrueSkillEvaluator:
    def __init__(self, eval_teams, regu_titles, regu_matches, home_advtg, draw_mrgn):
        self.teams = eval_teams
        self.regular_titles = regu_titles
        self.regular_matches = regu_matches
        self.home_adv = home_advtg
        self.draw_margin = draw_mrgn
        
    def home_adv_adjust(self):
        for match in self.regular_matches:
            wloc = match[self.regular_titles.index('Wloc')]
            if wloc == 'H':
                match[self.regular_titles.index('Wscore')] -= self.home_adv

    def startEvaluation(self):
        from trueskill import Rating, TrueSkill, rate_1vs1
        self.home_adv_adjust()
        draw_rates = self.calculate_draw_rate()
        results = dict()
        for score_diff in range(0, self.draw_margin):
##            env = TrueSkill(draw_probability = draw_rates[score_diff])
            env = TrueSkill(draw_probability = 0.0)
            team_rating = dict(zip(self.teams, [env.create_rating()] * len(self.teams)))
            for match in self.regular_matches:
                wteam = match[self.regular_titles.index('Wteam')]
                lteam = match[self.regular_titles.index('Lteam')]
                wscore = match[self.regular_titles.index('Wscore')]
                lscore = match[self.regular_titles.index('Lscore')]

                if wteam in team_rating and lteam in team_rating:
                    is_draw = False
##                    is_draw = abs(wscore - lscore) <= score_diff
                    if (wscore < lscore):
                        wteam, lteam = lteam, wteam
##                    if (wscore < lscore) and not is_draw:
##                        wteam, lteam = lteam, wteam
                    team_rating[wteam], team_rating[lteam] = rate_1vs1(team_rating[wteam],\
                        team_rating[lteam], drawn = is_draw, env = env)
                    
            probs = []
            for i in range(0, len(teams)):
                for j in range(i + 1, len(teams)):
                    prob = self.win_probability(team_rating[teams[i]], team_rating[teams[j]])
                    probs.append(prob)
            
            results[score_diff] = probs
        return results

    def calculate_draw_rate(self):
        draw_rates = dict()
        score_diff = 0
        while score_diff < self.draw_margin:
            num_draw = 0
            for recd in self.regular_matches:
                if abs(recd[regular_titles.index('Wscore')] - \
                   recd[regular_titles.index('Lscore')]) <= score_diff:
                    num_draw += 1
            draw_rates[score_diff] = num_draw / len(self.regular_matches)
            print(draw_rates[score_diff])
            score_diff += 1
        return draw_rates

    def win_probability(self, rating_a, rating_b):
        from trueskill import BETA
        from math import sqrt
        from trueskill.backends import cdf
        delta_mu = rating_a.mu - rating_b.mu
        denom = sqrt(2 * (BETA * BETA) + pow(rating_a.sigma, 2) \
                     + pow(rating_b.sigma, 2))
        return cdf(delta_mu / denom)


import csv
start_season = 2005
end_season = 2016
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
            row[regular_titles.index('Wscore')] = int(row[regular_titles.index('Wscore')])
            row[regular_titles.index('Lscore')] = int(row[regular_titles.index('Lscore')])
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

max_draw_margin = 1
max_home_adv = 3
home_adv = 2
while home_adv < max_home_adv:
    evaluator = TrueSkillEvaluator(teams, regular_titles, regular_matches, home_adv, max_draw_margin)
    results = evaluator.startEvaluation()
    for score_diff in results.keys():
        predict_res = list(zip(predict_matches, results[score_diff]))
        with open('results/' + str(home_adv) + "_" + str(score_diff) + '.csv', 'w', newline = '') as csvfile:
            writer = csv.writer(csvfile, quoting = csv.QUOTE_MINIMAL)
            writer.writerows(predict_titles)
            writer.writerows(predict_res)
    home_adv += 1
