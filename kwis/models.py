from django.db import models
from django.utils.translation import ugettext_lazy as _

# These models are defined:
# - Teams participating
# - Rounds in the quiz
# - Answered score per round for each team

class QTeam(models.Model):
    # A team only needs a name for identification
    team_name = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.team_name
    class Meta:
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')

class QRound(models.Model):
    # Each round has a name and a maximal score
    round_name = models.CharField(max_length=200, unique=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=1)
    def __str__(self):
        return self.round_name + ": " + str(self.max_score)
    class Meta:
        verbose_name = _('Round')
        verbose_name_plural = _('Rounds')

class QAnswer(models.Model):
    # Each answer is bound to a team, a round and contains the score for a specific team and round
    team = models.ForeignKey(QTeam,on_delete=models.PROTECT)
    rnd = models.ForeignKey(QRound,on_delete=models.PROTECT)
    score = models.DecimalField(max_digits=6, decimal_places=1)
    def __str__(self):
        return str(self.team) + ", " + self.rnd.round_name + ": " + str(self.score)
    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')

