from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django import forms

from decimal import *

from .models import QRound, QTeam, QAnswer

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
            round_status.append((r, "Complete"))
        else:
            round_status.append((r, "%d / %d" % (r.qanswer_set.count(), team_list.count())))

    context = {'round_list': round_status, 'team_list': team_list}
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
        caption = "Final ranking"
    elif len(rnd_complete) == 0:
        caption = "No results yet"
    else:
        caption = "Ranking after "
        for rnd in rnd_complete:
            caption += rnd.round_name + ", "
        caption = caption[:-2]

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

    return render(request, 'kwis/ranking.html', {'sorted': sorted_result, 'caption': caption})

# Detail views allow to view results per round or per team
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
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    fig = Figure()

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
    ax.bar(ind, scores, width, color='b')
    ax.bar(ind, maxima, width, color='w', bottom=scores)

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

