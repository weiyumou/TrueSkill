from TrueSkillEvaluator import TrueSkillEvaluator


class TestDriver:
    """
    A TestDriver is used to feed test parameters
    to a TrueSkillEvaluator. 
    """
    def __init__(self, tmatches, ateams, cteams):
        self.train_matches = tmatches
        self.all_teams = ateams
        self.curr_teams = cteams

    def start_test(self):
        mov = 11

        # Test parameters are passed as a list.
        eval_fields = [['to', 1.5, 2.0, 0.5, self.general_revs_adj],
                       ['loc', 7.0, 7.5, 0.5, self.home_advt_adj]]
        evaluator = TrueSkillEvaluator(self.curr_teams, self.all_teams,
                                       self.train_matches, eval_fields, mov)
        return evaluator.start_evaluation()

    # These are the static methods that determine
    # the effect of a particular feature on the MOV.
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
