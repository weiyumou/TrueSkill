import math
import trueskill


class TrueSkillEvaluator:
    def __init__(self, eval_teams, teams, eval_matches, eval_adj_fields, mov):
        self.evl_teams = eval_teams
        self.all_teams = teams
        self.matches = eval_matches
        self.adjust_overtime()
        self.matches_cpy = self.matches
        self.adj_fields = eval_adj_fields
        self.vic_margin = mov
        self.testings = dict()

    def start_evaluation(self):
        self.adjust_score(is_last=True)
        return self.testings

    def adjust_score(self, test_name='', is_last=False):
        if not self.adj_fields:
            return
        curr_adj = self.adj_fields.pop()
        score_eff = curr_adj[1]
        while score_eff < curr_adj[2]:
            test_name = '-' + curr_adj[0] + '-' + "{0:.1f}".format(score_eff).replace('.', '_') + test_name
            self.adjust_score(test_name)
            for match in self.matches_cpy:
                w_val = match['W' + curr_adj[0]]
                l_val = match['L' + curr_adj[0]] if ('L' + curr_adj[0]) in match else None
                curr_adj[4](w_val, l_val, score_eff, match)
            if is_last:
                self.testings[test_name] = self.predict(self.rate_team())
                self.matches_cpy = self.matches
                test_name = ''
            score_eff += curr_adj[3]

    def rate_team(self):
        trueskill.setup(draw_probability=self.draw_prob())
        ratings = dict(zip(self.all_teams, [trueskill.global_env().create_rating()] * len(self.all_teams)))
        for match in self.matches_cpy:
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

                while wscore - lscore >= self.vic_margin:
                    ratings[wteam], ratings[lteam] = \
                        trueskill.rate_1vs1(ratings[wteam], ratings[lteam], drawn=self.is_equal_score(wscore, lscore))
                    wscore -= self.vic_margin

        return ratings

    def draw_prob(self):
        num_draw = 0
        for match in self.matches_cpy:
            wscore = match['Wscore']
            lscore = match['Lscore']
            if self.is_equal_score(wscore, lscore):
                num_draw += 1
        return num_draw / len(self.matches_cpy)

    def predict(self, ratings):
        probs = []
        for i in range(0, len(self.evl_teams)):
            for j in range(i + 1, len(self.evl_teams)):
                prob = self.win_probability(ratings[self.evl_teams[i]], ratings[self.evl_teams[j]])
                if prob <= 0.1:
                    prob = 0.0
                elif prob >= 0.9:
                    prob = 1.0
                probs.append(prob)
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


# class HomeCourtAdv(NaiveEvaluator):
#     def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg):
#         super().__init__(eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj)
#         self.home_adv = home_advtg
#
#     def home_adv_adjust(self):
#         for match in self.regular_matches:
#             wloc = match[self.regular_titles.index('Wloc')]
#             if wloc == 'H':
#                 match[self.regular_titles.index('Wscore')] -= self.home_adv
#
#     def start_evaluation(self):
#         self.home_adv_adjust()
#         return super().start_evaluation()
#
#
# class OvertimeAsDraw(HomeCourtAdv):
#     def __init__(self, eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg):
#         super().__init__(eval_teams, regu_titles, regu_matches, vic_margin, l_adj, u_adj, home_advtg)
#
#     def adjust_overtime(self):
#         for match in self.regular_matches:
#             numot = match[self.regular_titles.index('Numot')]
#             if numot > 0:
#                 match[self.regular_titles.index('Wscore')] = match[self.regular_titles.index('Lscore')]
#
#     def start_evaluation(self):
#         self.adjust_overtime()
#         return super().start_evaluation()
