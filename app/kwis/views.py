from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django import forms
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required

from .models import Quiz, Round, Team, Answer
from .websocket_utils import trigger_refresh

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from decimal import Decimal

# Imports needed to generate graphs
import matplotlib as mpl
mpl.use('Agg')  # make sure no X backend is used

# Dictionary to define color usage in graphs
colors = {'score_good': 'green',
          'score_bad': 'red',
          'empty': 'lightblue',
          }


# Helper classes for forms
class PostedForm(forms.Form):
    score = forms.DecimalField(max_digits=6, decimal_places=1)


class ScoreForm(forms.Form):
    def __init__(self, max_value=None, *args, **kwargs):
        super(ScoreForm, self).__init__(*args, **kwargs)
        self.fields['score'] = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0, max_value=max_value)
        self.fields['score'].widget.attrs.update({"class": "uk-input"})

    score = forms.DecimalField(max_digits=6, decimal_places=1, min_value=0)


# Useful common functions
def get_completed_rounds():
    """
    Return a list of rounds that are completed by all teams.
    A completed round has as much elements in its answer_set as there are participating teams.
    """
    result = []
    for rnd in Round.objects.all():
        if rnd.answer_set.count() == Team.objects.count():
            result.append(rnd)
    return result


def get_ranked_results(completed_rounds):
    """
    For the rounds given in completed_rounds, calculate the total score for each team.
    Then all teams are sorted on total score and are given a ranking to allow for ex aequo scores.
    """
    results = []
    for team in Team.objects.all():
        teamtotal = 0
        for a in team.answer_set.all():
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
    if nbObjects <= 5:
        return "horizontal"
    else:
        # return "vertical"
        return 30


#   Initial views contain overviews only
def index(request):
    """
    List all teams and all rounds. This is the main jury view from where to add scores.
    """
    quiz_name = Quiz.objects.first().name
    round_list = Round.objects.all()
    team_list = Team.objects.all()

    round_status = []
    for r in round_list:
        if r.answer_set.count() == team_list.count():
            # Translators: This indicates all scores for a round have been entered
            round_status.append((r, _("Complete")))
        else:
            round_status.append((r, _("%(nrteams)d / %(totalteams)d teams") % {"nrteams": r.answer_set.count(), "totalteams": team_list.count()}))

    team_status = []
    for t in team_list:
        subtotal = 0
        maxtotal = 0
        for ts in t.answer_set.all():
            subtotal += ts.score
            maxtotal += ts.rnd.max_score
        team_status.append((t, "%.1f / %.1f" % (subtotal, maxtotal), subtotal))
    team_status.sort(key=lambda tup: tup[2], reverse=True)

    context = {'round_list': round_status, 'team_list': team_status, 'quiz_name': quiz_name}
    return render(request, 'index.html', context)


def ranking(request):
    """
    This is the main view for contestants: ranking of teams based on their results.
    """

    # First identify completed rounds.
    rnd_complete = get_completed_rounds()

    # Nothing to hide
    hidden = 0

    if len(rnd_complete) == Round.objects.count():
        # Translators: This indicates all scores for all rounds have been entered
        caption = _("Final ranking")
        # Hiding the final top 3 from the ranking view for dramatic effect
        quiz = Quiz.objects.first()
        hidden = max(0, 3 - quiz.reveal_count) if quiz else 3
    elif len(rnd_complete) == 0:
        # Translators: This indicates no round has all scores entered
        caption = _("No results yet")
    else:
        caption = _("Ranking after ")
        for rnd in rnd_complete:
            caption += rnd.round_name + ", "
        caption = caption[:-2]  # Remove final ", "

    ranking = get_ranked_results(rnd_complete)

    return render(request, 'ranking.html', {'sorted': ranking, 'caption': caption, 'hidden': hidden, 'quiz_name': Quiz.objects.first().name})


@login_required
def rnd_detail(request, rnd_id):
    """
    Detail views allow to view results per round or per team
    """
    rnd = get_object_or_404(Round, pk=rnd_id)

    # Filter a list of answers for this round
    ar = rnd.answer_set.all()

    # Create a list of teams that don't have a score in this round yet
    team_list_todo = []
    for t in Team.objects.order_by('team_name'):
        if ar.filter(team=t).count() == 0:
            team_list_todo.append(t)
    # Teams that already have a score in this round can be accessed from the template using the _set

    # Create form to be used for all other teams
    form = ScoreForm(max_value=rnd.max_score)

    return render(request, 'rnd_detail.html', {'rnd': rnd, 'team_list_todo': team_list_todo, 'form': form})


@login_required
def team_detail(request, team_id):
    """
    Detail views allow to view results per round or per team
    """
    # Check if team entry exists
    team = get_object_or_404(Team, pk=team_id)

    # Count all results for this team
    subtotal = 0
    maxtotal = 0
    alist = team.answer_set.order_by('rnd')
    for a in alist:
        subtotal += a.score
        maxtotal += a.rnd.max_score

    # Create a list of rounds that have no results yet for this team
    round_list_todo = []
    for r in Round.objects.all():
        if alist.filter(rnd=r).count() == 0:
            form = ScoreForm(max_value=r.max_score)
            round_list_todo.append((r, form))

    return render(request, 'team_detail.html', {'team': team, 'subtotal': subtotal, 'maxtotal': maxtotal, 'round_list_todo': round_list_todo})


@login_required
def vote(request, rnd_id, team_id):
    """
    The vote view handles the POST requests
    """
    # check for existing rnd and team
    arnd = get_object_or_404(Round, pk=rnd_id)
    ateam = get_object_or_404(Team, pk=team_id)

    # if item exists for Answer -> update; else create
    alist = Answer.objects.filter(rnd=arnd, team=ateam)
    if alist.count():
        a = alist.get()
    else:
        a = Answer(rnd=arnd, team=ateam, score="")

    # Get form
    if request.method == 'POST':
        form = PostedForm(request.POST)
        if form.is_valid():
            score = form.cleaned_data['score']

            # Primitive way to check correct value
            badvalue = 0
            if float(score) < 0 or float(score) > float(arnd.max_score):
                badvalue = 1

            if badvalue:
                form = ScoreForm(initial={'score': '0'})
            else:
                a.score = score
                a.save()

                return HttpResponseRedirect(reverse('rnd_detail', args=(arnd.id,)))

    else:
        form = ScoreForm(max_value=arnd.max_score, initial={'score': a.score})

    return render(request, 'form.html', {'rnd': arnd, 'team': ateam, 'form': form})


@login_required
def delete(request, rnd_id, team_id):
    """
    This function handles the deletion of an answer record
    """
    # check for existing rnd and team
    arnd = get_object_or_404(Round, pk=rnd_id)
    ateam = get_object_or_404(Team, pk=team_id)

    # if item exists for Answer -> delete
    alist = Answer.objects.filter(rnd=arnd, team=ateam)
    if alist.count():
        a = alist.get()
        a.delete()

    return HttpResponseRedirect(reverse('rnd_detail', args=(arnd.id,)))


@login_required
def reveal_next(request):
    """
    Reveal the next team in the ranking
    """
    quiz = Quiz.objects.first()
    if quiz and quiz.reveal_count < 3:
        quiz.reveal_count += 1
        quiz.save()

    trigger_refresh()
    return HttpResponseRedirect(reverse('index'))


def team_result(request, team_id):
    """
    Plot results per team
    """

    # Retrieve team info and scores for the team
    ateam = get_object_or_404(Team, pk=team_id)
    answers = ateam.answer_set.order_by('rnd')

    # Set number of vertical bars
    ind = np.arange(len(answers))

    # Retrieve score, max score and name per round
    scores = [answer.score for answer in answers]
    maxima = [(answer.rnd.max_score - answer.score) for answer in answers]
    names = [answer.rnd.round_name for answer in answers]

    # The image
    fig, ax = plt.subplots(1, 1)
    fig.set_tight_layout(True)

    # Draw vertical bars
    width = 0.25
    ax.bar(ind, scores, width, color=colors['score_good'])
    ax.bar(ind, maxima, width, color=colors['score_bad'], bottom=scores)

    # Set labels
    ax.set_xticks(ind)
    ax.set_xticklabels(names)
    ax.set_xlabel(_("Rounds"))
    ax.set_ylabel(_("Scores"))

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
    arnd = get_object_or_404(Round, pk=rnd_id)
    answers = arnd.answer_set.order_by('-score')

    # Set number of vertical bars
    ind = np.arange(len(answers))

    # Retrieve score and team name per round
    scores = [answer.score for answer in answers]
    names = [answer.team.team_name for answer in answers]

    # The image
    fig, ax = plt.subplots(1, 1)
    fig.set_tight_layout(True)

    # Draw vertical bar
    width = 0.25
    ax.barh(ind, scores, width, color=colors['score_good'])

    # Set labels
    ax.set_yticks(ind)
    ax.set_yticklabels(names)
    ax.set_ylabel(_("Teams"))
    ax.set_xlabel(_("Scores"))

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
    ind = np.arange(Team.objects.count())

    subtotals = []
    maxtotals = []
    names = []
    for t in Team.objects.all():
        subtotal = 0
        maxtotal = 0
        for ts in t.answer_set.all():
            subtotal += ts.score
            maxtotal += ts.rnd.max_score
        subtotals.append(Decimal(subtotal))
        maxtotals.append(maxtotal - subtotal)
        names.append(t.team_name)

    zipped = list(zip(subtotals, maxtotals, names))
    zipped.sort()
    if zipped:
        subtotals, maxtotals, names = zip(*zipped)

    # The image
    fig, ax = plt.subplots(1, 1)
    fig.set_tight_layout(True)  # Ensure labels fit in image

    # Draw bars
    width = 0.5
    ax.bar(ind, subtotals, width, color=colors['score_good'])
    ax.bar(ind, maxtotals, width, color=colors['score_bad'], bottom=subtotals)

    # Set labels
    ax.set_xticks(ind)
    ax.set_xticklabels(names, rotation=dynamic_rotation(Team.objects.count()), ha='right')
    ax.set_xlabel(_("Teams"))
    ax.set_ylabel(_("Cumulative score"))

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
    nbTeams = Team.objects.count()

    # Number of bars
    ind = np.arange(Round.objects.count())

    # Progress per round
    names = []  # Round names
    scores = []  # Effectively obtained by all teams per round
    maxima = []  # maxima for the already entered teams
    difference = []  # difference between maxima and scores obtained
    remaining = []  # max scores for teams not yet entered
    data = []  # raw score data in % for boxplot
    for r in Round.objects.all():
        names.append(r.round_name)
        rc = r.answer_set.count()

        rs = 0
        datalist = []
        for a in r.answer_set.all():
            rs += a.score
            datalist.append(float(a.score) / float(r.max_score))
        scores.append(rs)
        maxima.append(r.max_score * rc)
        difference.append(r.max_score * rc - rs)
        remaining.append(r.max_score * (nbTeams - rc))
        data.append(datalist)

    # The image
    fig, ax1 = plt.subplots(1, 1)
    fig.set_tight_layout(True)  # Ensure labels fit in image
    ax2 = ax1.twinx()

    # Draw bars
    barwidth = 0.5
    boxwidth = barwidth / 2
    barlocation = ind
    ax1.bar(barlocation, scores, barwidth, color=colors['score_good'])
    ax1.bar(barlocation, difference, barwidth, color=colors['score_bad'], bottom=scores)
    ax1.bar(barlocation, remaining, barwidth, color=colors['empty'], bottom=maxima)
    if data:
        ax2.boxplot(data, widths=boxwidth, positions=barlocation, showmeans=True)

    # Set labels
    ax1.set_xticks(ind)
    ax1.set_xticklabels(names, rotation=dynamic_rotation(Round.objects.count()), ha='center')
    ax1.set_xlabel(_("Rounds"))
    ax1.set_ylabel(_("Cumulative scores and progress"))
    ax2.set_ylabel(_("Statistics"))
    ax2.set_ylim([0, 1])

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
    round_names = []

    for comprnd in rnd_complete:
        increment_rnds.append(comprnd)
        ranking = get_ranked_results(increment_rnds)
        ranking_matrix.append(ranking)
        round_names.append(comprnd.round_name)

    # Team leading after most recent round: compose line with rankings over all other rounds
    # next team idem until all N lines composed
    N = 5  # Number of top teams to track
    if Team.objects.count() < N:
        # Limit N to the amount of teams
        N = Team.objects.count()
    top_positions = []
    team_names = []
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
    fig, ax1 = plt.subplots(1, 1, figsize=(7, 7))
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
