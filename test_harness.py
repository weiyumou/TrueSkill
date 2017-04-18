# pip3 install trueskill
# Docs: http://trueskill.org/

import csv
import re
import math
from copy import deepcopy
from TrueSkillEvaluator import TrueSkillEvaluator


class TestDriver:
    def __init__(self, tmatches, ateams, cteams):
        self.train_matches = tmatches
        self.all_teams = ateams
        self.curr_teams = cteams

    def start_test(self):
        mov = 11
        eval_fields = [['to', 1.5, 2.0, 0.5, self.general_revs_adj],
                       ['loc', 7.0, 7.5, 0.5, self.home_advt_adj]]
        evaluator = TrueSkillEvaluator(self.curr_teams, self.all_teams,
                                       self.train_matches, eval_fields, mov)
        return evaluator.start_evaluation()

    @staticmethod
    def general_adj(w_val, l_val, score_eff, match):
        if w_val > l_val:
            match['Wscore'] += score_eff
        elif w_val < l_val:
            match['Wscore'] -= score_eff

    @staticmethod
    def general_revs_adj(w_val, l_val, score_eff, match):
        if w_val < l_val:
            match['Wscore'] += score_eff
        elif w_val > l_val:
            match['Wscore'] -= score_eff

    @staticmethod
    def home_advt_adj(w_val, l_val, score_eff, match):
        if w_val == 'H':
            match['Wscore'] -= score_eff

# Get regular season match results
regular_matches = []
with open('dataset/RegularSeasonDetailedResults.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    field_names = reader.__next__()
    for row in reader:
        # season = int(row[field_names.index('Season')])
        # if start_season <= season <= end_season:
        new_row = [int(x) if x.isnumeric() else x for x in row]
        new_row[field_names.index('Wscore')] = float(row[field_names.index('Wscore')])
        new_row[field_names.index('Lscore')] = float(row[field_names.index('Lscore')])
        regular_matches.append(dict(zip(field_names, new_row)))

match_outcomes = dict()
with open('dataset/TourneyDetailedResults.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    field_names = reader.__next__()
    for row in reader:
        season = row[field_names.index('Season')]
        wteam = row[field_names.index('Wteam')]
        lteam = row[field_names.index('Lteam')]
        if wteam < lteam:
            match_outcomes[season + '_' + wteam + '_' + lteam] = 1
        else:
            match_outcomes[season + '_' + lteam + '_' + wteam] = 0

# Get matches to predict
predict_titles = []
with open('dataset/SampleSubmission.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    predict_titles.append(reader.__next__())
    for row in reader:
        match_outcomes[row[0]] = row[1]

# Get all teams
all_teams = []
with open('dataset/Teams.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    reader.__next__()
    for row in reader:
        all_teams.append(row[0])


def score(pred_pairs):
    s = 0.0
    for pair in pred_pairs:
        s += math.log(pair[0]) if pair[1] == 1 else math.log(1 - pair[0])
    return -s / len(pred_pairs)

start_season = 2003
end_season = 2014
time_window = 4

for season in range(start_season, end_season):
    curr_season = season + time_window - 1
    train_matches = []
    for recd in regular_matches:
        if season <= recd['Season'] <= curr_season:
            train_matches.append(recd)

    train_teams = set()
    pred_matches = []
    for key in match_outcomes.keys():
        if re.match(str(curr_season), key) is not None:
            str_split = key.split('_')
            train_teams.add(str_split[1])
            train_teams.add(str_split[2])
            pred_matches.append(key)

    team_lst = list(train_teams)
    team_lst.sort()
    pred_matches.sort()
    test_driver = TestDriver(deepcopy(train_matches), all_teams, team_lst)
    results = test_driver.start_test()

    for key in results.keys():
        test_name = str(curr_season) + '_' + key

        res = results[key]
        pred_probs = []
        pred_outcomes = []
        for item in res:
            key = str(curr_season) + '_' + item[0]
            if key in match_outcomes:
                pred_probs.append(item[1])
                pred_outcomes.append(match_outcomes[key])

        predict_res = list(zip(pred_matches, pred_probs))
        with open('results/' + test_name + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(predict_titles)
            writer.writerows(predict_res)

        eval_score = score(list(zip(pred_probs, pred_outcomes)))
        print(test_name + ': ' + str(eval_score))
