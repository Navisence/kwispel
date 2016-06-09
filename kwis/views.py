from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms
from django.forms import DecimalField

from decimal import *

from .models import QRound, QTeam, QAnswer

class ScoreForm(forms.Form):
    score = DecimalField(max_digits=6, decimal_places=1)

#   Initial views contain overviews only
def index(request):
    # List all teams and all rounds. This is the main jury view from where to add scores
    round_list = QRound.objects.all()
    team_list = QTeam.objects.all()
    context = {'round_list': round_list, 'team_list': team_list}
    return render(request, 'kwis/index.html', context)

def ranking(request):
    # This is the main view for contestants: ranking of teams based on their results
    result = []
    for team in QTeam.objects.all():
        teamtotal = 0
        for a in QAnswer.objects.filter(team = team):
            teamtotal += a.score
        result.append((team.team_name, teamtotal))

    # Sort
    sorted_result = sorted(result, reverse=True, key=lambda tup: tup[1])

    return render(request, 'kwis/ranking.html', {'sorted': sorted_result})

# Detail views allow to view results per round or per team
def rnd_detail(request, rnd_id):
    rnd = get_object_or_404(QRound, pk=rnd_id)

    # Filter a list of answers for this round
    ar = QAnswer.objects.filter(rnd = rnd)

    # Create a list of teams that don't have a score in this round yet
    team_list_todo = []
    for t in QTeam.objects.all():
        if ar.filter(team = t).count() == 0:
            team_list_todo.append(t)
    # Teams that already have a score in this round can be accessed from the template using the _set

    # Create form to be used for all other teams
    form = ScoreForm()

    return render(request, 'kwis/rnd_detail.html', {'rnd': rnd, 'team_list_todo': team_list_todo, 'form': form})

def team_detail(request, team_id):
    # Check if team entry exists
    team = get_object_or_404(QTeam, pk=team_id)

    # Count all results for this team
    subtotal = 0
    alist = QAnswer.objects.filter(team = team)
    for a in alist:
        subtotal += a.score

    # Create a list of rounds that have no results yet for this team
    round_list_todo = []
    for r in QRound.objects.all():
        if alist.filter(rnd = r).count() == 0:
            round_list_todo.append(r)

    # Create form to be used for empty rounds
    form = ScoreForm()

    return render(request, 'kwis/team_detail.html', {'team': team, 'subtotal': subtotal, 'round_list_todo': round_list_todo, 'form': form})

# The vote view handles the POST requests
def vote(request, rnd_id, team_id):
    # check for existing rnd and team
    arnd  = get_object_or_404(QRound, pk=rnd_id)
    ateam = get_object_or_404(QTeam, pk=team_id)

    # if item exists for QAnswer -> update; else create
    alist = QAnswer.objects.filter(rnd = arnd, team = ateam)
    if alist.count():
        a = alist.get()
    else:
        a = QAnswer(rnd = arnd, team = ateam, score="")

    # Get form
    if request.method == 'POST':
        form = ScoreForm(request.POST)
        if form.is_valid():

            # Modify score list
            score= form.cleaned_data['score']

            # Primitive way to check correct value
            badvalue = 0
            if float(score) < 0 or float(score) > float(arnd.max_score):
                badvalue = 1

            if badvalue:
                form = ScoreForm(initial={'score': '0'})
            else:
                a.score = score
                a.save()

                return HttpResponseRedirect(reverse('kwis:rnd_detail', args=(arnd.id,)))

    else:
        form = ScoreForm(initial={'score': a.score})

    return render(request, 'kwis/form.html', {'rnd': arnd, 'team': ateam, 'form': form})
