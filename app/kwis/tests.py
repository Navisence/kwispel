from django.test import TestCase
from kwis.models import Team, Round, Answer


# Create your tests here.
class KwisModelsTestCase(TestCase):
    def setUp(self):
        # Set up initial data for tests
        self.team1 = Team.objects.create(team_name="Team A")
        self.team2 = Team.objects.create(team_name="Team B")
        self.round1 = Round.objects.create(round_name="Round 1", max_score=100)
        self.round2 = Round.objects.create(round_name="Round 2", max_score=150)

    def test_team_creation(self):
        team = Team.objects.get(team_name="Team A")
        self.assertEqual(team.team_name, "Team A")

    def test_round_creation(self):
        rnd = Round.objects.get(round_name="Round 1")
        self.assertEqual(rnd.max_score, 100)

    def test_answer_creation(self):
        answer = Answer.objects.create(team=self.team1, rnd=self.round1, score=85)
        self.assertEqual(answer.score, 85)
        self.assertEqual(answer.team.team_name, "Team A")
        self.assertEqual(answer.rnd.round_name, "Round 1")

    def test_unique_team_round_answer_constraint(self):
        Answer.objects.create(team=self.team1, rnd=self.round1, score=90)
        with self.assertRaises(Exception):
            # Attempting to create a second answer for the same team and round should raise an error
            Answer.objects.create(team=self.team1, rnd=self.round1, score=95)
