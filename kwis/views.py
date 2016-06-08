from django.shortcuts import render

from .models import QRound, QTeam, QAnswer

#   Initial views contain overviews only
def index(request):
    # List all teams and all rounds
    round_list = QRound.objects.all()
    team_list = QTeam.objects.all()
    context = {'round_list': round_list, 'team_list': team_list}
    return render(request, 'kwis/index.html', context)

def ranking(request):
    result = []
    for team in QTeam.objects.all():
        teamtotal = 0
        for a in QAnswer.objects.filter(team = team):
            teamtotal += a.score
        result.append((team.team_name, teamtotal))

    # Sort
    sorted_result = sorted(result, reverse=True, key=lambda tup: tup[1])

    return render(request, 'kwis/ranking.html', {'sorted': sorted_result})

