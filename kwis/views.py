from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from decimal import *

from .models import QRound, QTeam, QAnswer

# Imports needed to generate graphs
import matplotlib as mpl
mpl.use('Agg') # make sure no X backend is used

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


# Dictionary to define color usage in graphs
colors  = {'score_good': 'green',
        'score_bad': 'red',
        'empty':'lightblue'}

# Helper classes for forms
class PostedForm(forms.Form):
    score = forms.DecimalField(max_digits=6, decimal_places=1)

class ScoreForm(forms.Form):
    def __init__(self, max_value=None, *args, **kwargs):
        super(ScoreForm, self).__init__(*args, **kwargs)
        self.fields['score'] = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, max_value=max_value)

    score = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0)

# Useful common functions
def get_completed_rounds():
    """
    Return a list of rounds that are completed by all teams.
    A completed round has as much elements in its qanswer_set as there are participating teams.
    """
    result = []
    for rnd in QRound.objects.all():
        if rnd.qanswer_set.count() == QTeam.objects.count():
            result.append(rnd)
    return result

def get_ranked_results(completed_rounds):
    """
    For the rounds given in completed_rounds, calculate the total score for each team.
    Then all teams are sorted on total score and are given a ranking to allow for ex aequo scores.
    """
    results = []
    for team in QTeam.objects.all():
        teamtotal = 0
        for a in team.qanswer_set.all():
            # Only add results for complete rounds
            if a.rnd in completed_rounds:
                teamtotal += a.score
        results.append((team.team_name, teamtotal))

    # Sort the results
    sorted_results = sorted(results, reverse=True, key=lambda tup: tup[1])

    rank, count, previous, ranking = 0, 0, None, []
    for key, num in sorted_results:
        count += 1
        if num != previous:
            rank += count
            previous = num
            count = 0
        ranking.append((rank, key, num))

    return ranking

def dynamic_rotation(nbObjects):
    if nbObjects <= 10:
        return "-25"
    elif nbObjects <= 20:
        return "-35"
    else:
        return "-45"

#   Initial views contain overviews only
def index(request):
    """
    List all teams and all rounds. This is the main jury view from where to add scores
    """
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
    """
    This is the main view for contestants: ranking of teams based on their results
    """

    # First identify completed rounds.
    rnd_complete = get_completed_rounds()

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

    ranking = get_ranked_results(rnd_complete)

    return render(request, 'kwis/ranking.html', {'sorted': ranking, 'caption': caption})

@login_required
def rnd_detail(request, rnd_id):
    """
    Detail views allow to view results per round or per team
    """
    rnd = get_object_or_404(QRound, pk=rnd_id)

    # Filter a list of answers for this round
    ar = rnd.qanswer_set.all()

    # Create a list of teams that don't have a score in this round yet
    team_list_todo = []
    for t in QTeam.objects.order_by('team_name'):
        if ar.filter(team = t).count() == 0:
            team_list_todo.append(t)
    # Teams that already have a score in this round can be accessed from the template using the _set

    # Create form to be used for all other teams
    form = ScoreForm(max_value=rnd.max_score)

    return render(request, 'kwis/rnd_detail.html', {'rnd': rnd, 'team_list_todo': team_list_todo, 'form': form})

@login_required
def team_detail(request, team_id):
    """
    Detail views allow to view results per round or per team
    """
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

@login_required
def vote(request, rnd_id, team_id):
    """
    The vote view handles the POST requests
    """
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
    """
    Plot results per team
    """

    # Retrieve team info and scores for the team
    ateam = get_object_or_404(QTeam, pk=team_id)
    answers = ateam.qanswer_set.order_by('rnd')

    # Set number of vertical bars
    ind = np.arange(len(answers))

    # Retrieve score, max score and name per round
    scores = [answer.score for answer in answers]
    maxima = [(answer.rnd.max_score - answer.score) for answer in answers]
    names  = [answer.rnd.round_name for answer in answers]

    # The image
    fig, ax = plt.subplots(1,1)
    fig.set_tight_layout(True)

    # Draw vertical bars
    width = 0.25
    ax.bar(ind, scores, width, color=colors['score_good'])
    ax.bar(ind, maxima, width, color=colors['score_bad'], bottom=scores)

    # Set labels and title
    ax.set_xticks(ind + width/2)
    ax.set_xticklabels(names)
    ax.set_xlabel(_("Rounds"))
    ax.set_ylabel(_("Scores"))

    title = _(u"Scores for %s") % ateam.team_name
    ax.set_title(title)

    ax.grid(True)
    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def rnd_result(request, rnd_id):
    """
    Plot results per round
    """

    # Retrieve round info and scores for round
    arnd = get_object_or_404(QRound, pk=rnd_id)
    answers = arnd.qanswer_set.order_by('-score')

    # Set number of vertical bars
    ind = np.arange(len(answers))

    # Retrieve score and team name per round
    scores = [answer.score for answer in answers]
    names  = [answer.team.team_name for answer in answers]

    # The image
    fig, ax = plt.subplots(1,1)
    fig.set_tight_layout(True)

    # Draw vertical bar
    width = 0.25
    ax.barh(ind, scores, width, color=colors['score_good'])

    # Set labels and title
    ax.set_yticks(ind + width/2)
    ax.set_yticklabels(names)
    ax.set_ylabel(_("Teams"))
    ax.set_xlabel(_("Scores"))

    title = _(u"Scores for %s") % arnd.round_name
    ax.set_title(title)

    ax.grid(True)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def team_overview(request):
    """
    Plot overview of all teams
    """

    # Cumulative scores per team
    ind = np.arange(QTeam.objects.count())

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

    zipped = list(zip(subtotals, maxtotals, names))
    zipped.sort()
    subtotals, maxtotals, names = zip(*zipped)

    # The image
    fig, ax = plt.subplots(1,1)
    fig.set_tight_layout(True)

    # Draw bars
    width = 0.5
    ax.bar(ind, subtotals, width, color=colors['score_good'])
    ax.bar(ind, maxtotals, width, color=colors['score_bad'], bottom=subtotals)

    # Set labels and title
    ax.set_xticks(ind + width/2)
    ax.set_xticklabels(names, rotation=dynamic_rotation(QTeam.objects.count()), ha='left')
    ax.set_xlabel(_("Teams"))
    ax.set_ylabel(_("Cumulative score"))

    title = _(u"Progress per team")
    ax.set_title(title)

    ax.grid(True)

    for tl in ax.get_yticklabels():
        tl.set_color(colors['score_good'])

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

def rnd_overview(request):
    """
    Plot overview of all rounds
    """

    # Number of teams determines max level of round completion
    nbTeams = QTeam.objects.count()

    # Number of bars
    ind = np.arange(QRound.objects.count())

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
    ax1.set_xticklabels(names, rotation=dynamic_rotation(QRound.objects.count()), ha='left')
    ax1.set_xlabel(_("Rounds"))
    ax1.set_ylabel(_("Cumulative scores and progress"))
    ax2.set_ylabel(_("Statistics"))
    ax2.set_ylim([0,1])

    title = _(u"Progress per round")
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

def ranking_overview(request):
    """
    Show history of rankings for top N teams in current ranking
    """

    # Check which rounds are complete
    rnd_complete = get_completed_rounds()

    # Calculate ranking after each of these rounds
    increment_rnds = []
    ranking_matrix = []
    round_names    = []

    for comprnd in rnd_complete:
        increment_rnds.append(comprnd)
        ranking = get_ranked_results(increment_rnds)
        ranking_matrix.append(ranking)
        round_names.append(comprnd.round_name)

    # Team leading after most recent round: compose line with rankings over all other rounds
    # next team idem until all N lines composed
    N = 5 # Number of top teams to track
    if QTeam.objects.count() < N:
        # Limit N to the amount of teams
        N = QTeam.objects.count()
    top_positions = []
    team_names    = []
    if ranking_matrix:
        for i in range(N):
            position_list = []
            # Find the name of the team that finished N + 1
            tn = ranking_matrix[-1][i][1]
            # Find the positions of this team over all rounds
            for ranking in ranking_matrix:
                ti = [x for x in ranking if tn in x][0]
                position_list.append(ranking.index(ti) + 1)

            top_positions.append(position_list)
            team_names.append(tn)

    # matrix transpose for easier plotting
    position_sequence = [list(i) for i in zip(*top_positions)]

    # The image
    fig, ax1 = plt.subplots(1,1,figsize=(7,7))
    fig.set_tight_layout(True)

    # Invert y axis so that leading team is on top
    ax1.invert_yaxis()

    ax1.plot(position_sequence, linewidth=2)
    ind = np.arange(len(round_names))
    ax1.set_xticks(ind)
    ax1.set_xticklabels(round_names)
    ax1.tick_params(axis='both', which='both', labelbottom=True, labeltop=False, labelleft=True, labelright=True)
    ax1.set_xlabel(_("Round"))
    ax1.set_ylabel(_("Position"))
    ax1.legend(team_names, loc='best')
    ax1.grid(True)

    canvas = FigureCanvas(fig)
    response = HttpResponse(content_type='image/png')

    canvas.print_png(response)
    return response

