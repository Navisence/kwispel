from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from decimal import *

from .models import QRound, QTeam, QAnswer

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


# Dictionary to define color usage in graphs
colors  = {'score_good': 'green',
        'score_bad': 'red',
        'empty':'lightblue'}

class PostedForm(forms.Form):
    score = forms.DecimalField(max_digits=6, decimal_places=1)

class ScoreForm(forms.Form):
    def __init__(self, max_value=None, *args, **kwargs):
        super(ScoreForm, self).__init__(*args, **kwargs)
        self.fields['score'] = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, max_value=max_value)

    score = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0)

#   Initial views contain overviews only
def index(request):
    # List all teams and all rounds. This is the main jury view from where to add scores
    round_list = QRound.objects.all()
    team_list = QTeam.objects.all()

    round_status = []
    for r in round_list:
        if r.qanswer_set.count() == team_list.count():
            # Translators: This indicates all scores for a round have been entered
            round_status.append((r, _("Complete")))
        else:
            round_status.append((r, "%d / %d" % (r.qanswer_set.count(), team_list.count())))

    team_status = []
    for t in team_list:
        subtotal = 0
        maxtotal = 0
        for ts in t.qanswer_set.all():
            subtotal += ts.score
            maxtotal += ts.rnd.max_score
        team_status.append((t, "%.1f / %.1f" % (subtotal, maxtotal)))

    context = {'round_list': round_status, 'team_list': team_status}
    return render(request, 'kwis/index.html', context)

def ranking(request):
    # This is the main view for contestants: ranking of teams based on their results

    # First identify completed rounds. A completed round has as much elements in its
    # qanswer_set as there are participating teams.
    rnd_complete = []
    for rnd in QRound.objects.all():
        if rnd.qanswer_set.count() == QTeam.objects.count():
            rnd_complete.append(rnd)

    if len(rnd_complete) == QRound.objects.count():
        # Translators: This indicates all scores for all rounds have been entered
        caption = _("Final ranking")
    elif len(rnd_complete) == 0:
        # Translators: This indicates no round has all scores entered
        caption = _("No results yet")
    else:
        caption = _("Ranking after ")
        for rnd in rnd_complete:
            caption += rnd.round_name + ", "
        caption = caption[:-2] # Remove final ", "

    result = []
    for team in QTeam.objects.all():
        teamtotal = 0
        for a in team.qanswer_set.all():
            # Only add results for complete rounds
            if a.rnd in rnd_complete:
                teamtotal += a.score
        result.append((team.team_name, teamtotal))

    # Sort
    sorted_result = sorted(result, reverse=True, key=lambda tup: tup[1])

    rank, count, previous, ranked_result = 0, 0, None, []
    for key, num in sorted_result:
        count += 1
        if num != previous:
            rank += count
            previous = num
            count = 0
        ranked_result.append((rank, key, num))

    return render(request, 'kwis/ranking.html', {'sorted': ranked_result, 'caption': caption})

# Detail views allow to view results per round or per team
@login_required
def rnd_detail(request, rnd_id):
    rnd = get_object_or_404(QRound, pk=rnd_id)

    # Filter a list of answers for this round
    ar = rnd.qanswer_set.all()

    # Create a list of teams that don't have a score in this round yet
    team_list_todo = []
    for t in QTeam.objects.all():
        if ar.filter(team = t).count() == 0:
            team_list_todo.append(t)
    # Teams that already have a score in this round can be accessed from the template using the _set

    # Create form to be used for all other teams
    form = ScoreForm(max_value=rnd.max_score)

    return render(request, 'kwis/rnd_detail.html', {'rnd': rnd, 'team_list_todo': team_list_todo, 'form': form})

@login_required
def team_detail(request, team_id):
    # Check if team entry exists
    team = get_object_or_404(QTeam, pk=team_id)

    # Count all results for this team
    subtotal = 0
    maxtotal = 0
    alist = team.qanswer_set.order_by('rnd')
    for a in alist:
        subtotal += a.score
        maxtotal += a.rnd.max_score

    # Create a list of rounds that have no results yet for this team
    round_list_todo = []
    for r in QRound.objects.all():
        if alist.filter(rnd = r).count() == 0:
            form = ScoreForm(max_value=r.max_score)
            round_list_todo.append((r, form))

    return render(request, 'kwis/team_detail.html', {'team': team, 'subtotal': subtotal, 'maxtotal': maxtotal, 'round_list_todo': round_list_todo})

# The vote view handles the POST requests
@login_required
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
        form = PostedForm(request.POST)
        if form.is_valid():
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
        form = ScoreForm(max_value=arnd.max_score, initial={'score': a.score})

    return render(request, 'kwis/form.html', {'rnd': arnd, 'team': ateam, 'form': form})

def team_result(request, team_id):
    fig = Figure()
    fig.set_tight_layout(True)
    ax = fig.add_subplot(1,1,1)

    # Retrieve team info and scores for the team
    ateam = get_object_or_404(QTeam, pk=team_id)
    answers = ateam.qanswer_set.order_by('rnd')

    # Set number of vertical bars
    ind = matplotlib.numpy.arange(len(answers))

    # Retrieve score, max score and name per round
    scores = [answer.score for answer in answers]
    maxima = [(answer.rnd.max_score - answer.score) for answer in answers]
    names  = [answer.rnd.round_name for answer in answers]

    width = 0.25

    # Draw vertical bars
    ax.bar(ind, scores, width, color=colors['score_good'])
    ax.bar(ind, maxima, width, color=colors['score_bad'], bottom=scores)

    # Set labels and title
    ax.set_xticks(ind + width/2)
    ax.set_xticklabels(names)
    ax.set_xlabel("Rounds")
    ax.set_ylabel("Scores")

    title = u"Scores for %s" % ateam.team_name
    ax.set_title(title)

    ax.grid(True)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def rnd_result(request, rnd_id):
    fig = Figure()
    fig.set_tight_layout(True)
    ax = fig.add_subplot(1,1,1)

    # Retrieve round info and scores for round
    arnd = get_object_or_404(QRound, pk=rnd_id)
    answers = arnd.qanswer_set.order_by('-team')

    # Set number of vertical bars
    ind = matplotlib.numpy.arange(len(answers))

    # Retrieve score and team name per round
    scores = [answer.score for answer in answers]
    names  = [answer.team.team_name for answer in answers]

    width = 0.25

    # Draw vertical bar
    ax.barh(ind, scores, width, color=colors['score_good'])

    # Set labels and title
    ax.set_yticks(ind + width/2)
    ax.set_yticklabels(names)
    ax.set_ylabel("Teams")
    ax.set_xlabel("Scores")

    title = u"Scores for %s" % arnd.round_name
    ax.set_title(title)

    ax.grid(True)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def team_overview(request):
    fig = Figure()
    fig.set_tight_layout(True)
    ax1 = fig.add_subplot(1,1,1)

    # Cumulative scores per team
    ind = matplotlib.numpy.arange(QTeam.objects.count())

    subtotals = []
    maxtotals = []
    names     = []
    for t in QTeam.objects.all():
        subtotal = 0
        maxtotal = 0
        for ts in t.qanswer_set.all():
            subtotal += ts.score
            maxtotal += ts.rnd.max_score
        subtotals.append(subtotal)
        maxtotals.append(maxtotal - subtotal)
        names.append(t.team_name)

    width = 0.5

    # Draw bars
    ax1.bar(ind, subtotals, width, color=colors['score_good'])
    ax1.bar(ind, maxtotals, width, color=colors['score_bad'], bottom=subtotals)

    # Set labels and title
    ax1.set_xticks(ind + width/2)
    ax1.set_xticklabels(names, rotation="-25", ha='left')
    ax1.set_xlabel("Teams")
    ax1.set_ylabel("Cumulative score")

    title = u"Progress per team"
    ax1.set_title(title)

    ax1.grid(True)

    for tl in ax1.get_yticklabels():
        tl.set_color(colors['score_good'])

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def rnd_overview(request):
    import numpy as np
    import matplotlib.pyplot as plt

    # Number of teams determines max level of round completion
    nbTeams = QTeam.objects.count()

    # Number of bars
    ind = matplotlib.numpy.arange(QRound.objects.count())

    # Progress per round
    names      = [] # Round names
    scores     = [] # Effectively obtained by all teams per round
    maxima     = [] # maxima for the already entered teams
    difference = [] # difference between maxima and scores obtained
    remaining  = [] # max scores for teams not yet entered
    data       = [] # raw score data in % for boxplot
    for r in QRound.objects.all():
        names.append(r.round_name)
        rc = r.qanswer_set.count()

        rs = 0
        datalist = []
        for a in r.qanswer_set.all():
            rs += a.score
            datalist.append(float(a.score)/float(r.max_score))
        scores.append(rs)
        maxima.append(r.max_score * rc)
        difference.append(r.max_score * rc - rs)
        remaining.append(r.max_score * (nbTeams - rc))
        data.append(datalist)

    # The image
    fig, ax1 = plt.subplots(1,1)
    fig.set_tight_layout(True)
    ax2 = ax1.twinx()

    # Draw bars
    width = 0.25
    barlocation = ind-width
    boxlocation = ind+width
    ax1.bar(barlocation, scores, width, color=colors['score_good'])
    ax1.bar(barlocation, difference, width, color=colors['score_bad'], bottom=scores)
    ax1.bar(barlocation, remaining, width, color=colors['empty'], bottom=maxima)
    ax2.boxplot(data, widths=width, positions=boxlocation, showmeans=True)

    # Set labels and title
    ax1.set_xticks(ind)
    ax1.set_xticklabels(names, rotation="-25", ha='left')
    ax1.set_xlabel("Rounds")
    ax1.set_ylabel("Cumulative scores and progress")
    ax2.set_ylabel("Statistics")
    ax2.set_ylim([0,1])

    title = u"Progress per round"
    ax1.set_title(title)

    ax1.grid(True)

    for tl in ax1.get_yticklabels():
        tl.set_color(colors['score_good'])

    for tl in ax2.get_yticklabels():
        tl.set_color(colors['score_bad'])

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

