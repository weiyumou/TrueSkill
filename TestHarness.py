# pip3 install trueskill
# Docs: http://trueskill.org/
# This file contains codes to run the TestDriver
# as well as the TrueSkillEvaluator

import csv
import re
import math
from copy import deepcopy
from TestDriver import TestDriver


# Get regular season match results
regular_matches = []
with open('dataset/RegularSeasonDetailedResults.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    field_names = reader.__next__()
    for row in reader:
        new_row = [int(x) if x.isnumeric() else x for x in row]
        new_row[field_names.index('Wscore')] = float(row[field_names.index('Wscore')])
        new_row[field_names.index('Lscore')] = float(row[field_names.index('Lscore')])
        regular_matches.append(dict(zip(field_names, new_row)))

# This part is supposed to obtain Tournament match outcomes
# over the years to conduct simulated competitions.
# But it is disabled for the purpose of submission.
match_outcomes = dict()
# with open('dataset/TourneyDetailedResults.csv', newline='') as csvfile:
#     reader = csv.reader(csvfile, delimiter=',')
#     field_names = reader.__next__()
#     for row in reader:
#         season = row[field_names.index('Season')]
#         wteam = row[field_names.index('Wteam')]
#         lteam = row[field_names.index('Lteam')]
#         if wteam < lteam:
#             match_outcomes[season + '_' + wteam + '_' + lteam] = 1
#         else:
#             match_outcomes[season + '_' + lteam + '_' + wteam] = 0

# Load the 2016 matches to predict
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


# def score(pred_pairs):
#     """
#
#     This function is used to score a submission
#     in a simulated competition and disabled for
#     the propose of submission.
#     """
#     s = 0.0
#     for pair in pred_pairs:
#         s += math.log(pair[0]) if pair[1] == 1 else math.log(1 - pair[0])
#     return -s / len(pred_pairs)

start_season = 2013
end_season = 2014
time_window = 4

for season in range(start_season, end_season):
    curr_season = season + time_window - 1

    # Get training data for the current season
    train_matches = []
    for recd in regular_matches:
        if season <= recd['Season'] <= curr_season:
            train_matches.append(recd)

    # Get the matches to predict
    # as well as the teams involved.
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

    # Create a TestDriver to invoke a TrueSkillEvaluator
    test_driver = TestDriver(deepcopy(train_matches), all_teams, team_lst)
    results = test_driver.start_test()

    # min_score = math.inf
    # min_test_name = ''
    for key in results.keys():
        test_name = str(curr_season) + '_' + key

        # For each test, obtain the predicted probabilities
        res = results[key]
        pred_probs = []
        pred_outcomes = []
        for item in res:
            key = str(curr_season) + '_' + item[0]
            if key in match_outcomes:
                pred_probs.append(item[1])
                pred_outcomes.append(match_outcomes[key])

        # Write the predictions into designated files
        predict_res = list(zip(pred_matches, pred_probs))
        with open('results/' + test_name + '.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(predict_titles)
            writer.writerows(predict_res)

        # This part is for simulated competitions.

        # eval_score = score(list(zip(pred_probs, pred_outcomes)))
        # if min_score - eval_score > 1e-7:
        #     min_score = eval_score
        #     min_test_name = test_name

    # print(min_test_name + ': ' + str(min_score))
