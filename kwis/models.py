from django.db import models

# These models are defined:
# - Teams participating
# - Rounds in the quiz
# - Answered scores per round for each team

class QTeam(models.Model):
    # A team only needs a name for identification
    team_name = models.CharField(max_length=200)
    def __str__(self):
        return self.team_name

class QRound(models.Model):
    # Each round has a name and a maximal score
    round_name = models.CharField(max_length=200)
    max_score = models.DecimalField(max_digits=6, decimal_places=1)
    def __str__(self):
        return self.round_name + ": " + str(self.max_score)

class QAnswer(models.Model):
    # Each answer is bound to a team, a round and contains the score for a specific team and round
    team = models.ForeignKey(QTeam)
    rnd = models.ForeignKey(QRound)
    score = models.DecimalField(max_digits=6, decimal_places=1)
    def __str__(self):
        return str(self.team) + ", " + self.rnd.round_name + ": " + str(self.score)

