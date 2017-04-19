import math
import trueskill
from copy import deepcopy


class TrueSkillEvaluator:
    """
    A TrueSkillEvaluator is used to run the backend
    TrueSkill algorithm to calculate the winning
    probabilities. 
    """
    def __init__(self, eval_teams, teams, eval_matches, eval_adj_fields, mov):
        self.evl_teams = eval_teams
        self.all_teams = teams
        self.matches = eval_matches
        self.adjust_overtime()
        self.adj_fields = eval_adj_fields
        self.vic_margin = mov
        self.testings = dict()

    def start_evaluation(self):
        self.adjust_score(self.matches, self.adj_fields)
        return self.testings

    def adjust_score(self, matches, adj_fields, base_name=''):
        """
        This function recursively applies the test parameters
        to run multiple tests. 
        """
        curr_adj = adj_fields.pop()
        score_eff = curr_adj[1]
        while abs(score_eff - curr_adj[2]) >= 1e-7:
            for match in matches:
                w_val = match['W' + curr_adj[0]]
                l_val = match['L' + curr_adj[0]] if ('L' + curr_adj[0]) in match else None
                curr_adj[4](w_val, l_val, score_eff if score_eff == curr_adj[1] else curr_adj[3], match)
            test_name = curr_adj[0] + '-' + "{0:.1f}".format(score_eff).replace('.', '_') + '-' + base_name
            if adj_fields:
                self.adjust_score(matches, deepcopy(adj_fields), test_name)
            else:
                self.testings[test_name] = self.predict(self.rate_team(deepcopy(matches)))
            score_eff += curr_adj[3]

    def rate_team(self, matches):
        """
        This function runs the TrueSkill rating system to
        determine the skill estimates of each team. 
        """
        trueskill.setup(draw_probability=self.draw_prob(matches))
        ratings = dict(zip(self.all_teams, [trueskill.global_env().create_rating()] * len(self.all_teams)))
        for match in matches:
            wteam = str(match['Wteam'])
            lteam = str(match['Lteam'])
            wscore = match['Wscore']
            lscore = match['Lscore']

            if wteam in ratings and lteam in ratings:
                if wscore < lscore:
                    wteam, lteam = lteam, wteam
                    wscore, lscore = lscore, wscore

                ratings[wteam], ratings[lteam] = \
                    trueskill.rate_1vs1(ratings[wteam], ratings[lteam], drawn=self.is_equal_score(wscore, lscore))
                wscore -= self.vic_margin

                # while wscore - lscore >= self.vic_margin:
                #     ratings[wteam], ratings[lteam] = \
                #         trueskill.rate_1vs1(ratings[wteam], ratings[lteam], drawn=self.is_equal_score(wscore, lscore))
                #     wscore -= self.vic_margin

        return ratings

    def draw_prob(self, matches):
        num_draw = 0
        for match in matches:
            wscore = match['Wscore']
            lscore = match['Lscore']
            if self.is_equal_score(wscore, lscore):
                num_draw += 1
        return num_draw / len(matches)

    def predict(self, ratings):
        probs = []
        for i in range(0, len(self.evl_teams)):
            for j in range(i + 1, len(self.evl_teams)):
                prob = self.win_probability(ratings[self.evl_teams[i]], ratings[self.evl_teams[j]])
                # if prob <= 0.1:
                #     prob = 0.0
                # elif prob >= 0.9:
                #     prob = 1.0
                probs.append((self.evl_teams[i] + '_' + self.evl_teams[j], prob))
        return probs

    def adjust_overtime(self):
        for match in self.matches:
            if match['Numot'] > 0:
                match['Wscore'] = match['Lscore']

    @staticmethod
    def is_equal_score(wscore, lscore):
        return abs(wscore - lscore) <= 1e-7

    @staticmethod
    def win_probability(rating_a, rating_b):
        delta_mu = rating_a.mu - rating_b.mu
        denom = math.sqrt(2 * (trueskill.BETA * trueskill.BETA) + pow(rating_a.sigma, 2) \
                          + pow(rating_b.sigma, 2))
        return trueskill.backends.cdf(delta_mu / denom)

