from django.db import models
from django.utils.translation import gettext_lazy as _

# These models are defined:
# - Quiz for storing state of a quiz
# - Teams participating
# - Rounds in the quiz
# - Answered score per round for each team


class Quiz(models.Model):
    name = models.CharField(max_length=200)
    reveal_count = models.IntegerField(default=0)  # Number of top teams to reveal in final ranking

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')


class Team(models.Model):
    # A team only needs a name for identification
    team_name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.team_name

    class Meta:
        # The name for team in single and plural form
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')


class Round(models.Model):
    # Each round has a name and a maximal score
    round_name = models.CharField(max_length=200, unique=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=1)

    def __str__(self):
        return self.round_name + ": " + str(self.max_score)

    class Meta:
        verbose_name = _('Round')
        verbose_name_plural = _('Rounds')


class Answer(models.Model):
    # Each answer is bound to a team, a round and contains the score for a specific team and round
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rnd = models.ForeignKey(Round, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=1)

    def __str__(self):
        return str(self.team) + ", " + self.rnd.round_name + ": " + str(self.score)

    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        constraints = [
            # Ensure that each team can only have one answer per round
            models.UniqueConstraint(
                fields=['team', 'rnd'],
                name='unique_team_round_answer',
                violation_error_message=_("A team can only have one answer per round.")
            ),
        ]
