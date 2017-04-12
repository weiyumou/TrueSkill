# pip3 install trueskill
# Docs: http://trueskill.org/

import csv
from TrueSkillEvaluator import TrueSkillEvaluator

start_season = 2013
end_season = 2016  # inclusive

# Get matches to predict
predict_titles = []
predict_matches = []
with open('dataset/SampleSubmission.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    predict_titles.append(reader.__next__())
    for row in reader:
        predict_matches.append(row[0])

predict_teams = predict_matches[0].split('_')[1:]
for recd in predict_matches[1:]:
    ret = recd.split('_')
    if ret[1] == predict_teams[0]:
        predict_teams.append(ret[2])
    else:
        break

# Get all teams
all_teams = []
with open('dataset/Teams.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    reader.__next__()
    for row in reader:
        all_teams.append(row[0])

# Get regular season match results
regular_matches = []
with open('dataset/RegularSeasonDetailedResults.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    field_names = reader.__next__()
    for row in reader:
        season = int(row[field_names.index('Season')])
        if start_season <= season <= end_season:
            new_row = [int(x) if x.isnumeric() else x for x in row]
            new_row[field_names.index('Wscore')] = float(row[field_names.index('Wscore')])
            new_row[field_names.index('Lscore')] = float(row[field_names.index('Lscore')])
            regular_matches.append(dict(zip(field_names, new_row)))


def home_adv_adjust(w_val, l_val, score_eff, match):
    if w_val == 'H':
        match['Wscore'] -= score_eff

offe_eval_fields = [['loc', 2.0, 2.5, 0.1, home_adv_adjust]]
offe_evaluator = TrueSkillEvaluator(predict_teams, all_teams, regular_matches, offe_eval_fields, 11)
results = offe_evaluator.start_evaluation()
for test in results.keys():
    predict_res = list(zip(predict_matches, results[test]))
    with open('results/' + test + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(predict_titles)
        writer.writerows(predict_res)

