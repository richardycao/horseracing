import re
import pandas as pd

def find_value_in_html(html, left, right, width=20):
    return [[html[i.end():i.end()+j.start()] for j in re.finditer(right, html[i.end(): i.end() + width])][0] for i in re.finditer(left, html)]

def pad_or_trunc(arr, target_len):
    return arr[:target_len] + ['-']*(target_len - len(arr))

def apply_scratch(arr, scratched):
    i = 0
    result = []
    for s in scratched:
        if not s:
            result.append(arr[i])
            i += 1
        else:
            result.append('-')
    return result

def find_scratched(html, query):
    return [len([k for k in re.finditer('class="h5 text-scratched"', j)]) for j in [html[i.start():i.end()] for i in re.finditer(query, html)]]

##############################

def details():
    with open('details.txt', 'r') as f:
        html = f.read()
    dist = find_value_in_html(html, left='<li ng-bind="data.distance">', right='</li>')
    racetype = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.raceType.Name">', right='</li>')
    raceclass = find_value_in_html(html, left='<span ng-bind="data.currentRace.raceClass">', right='</span>')
    surface = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.surfaceName">', right='</li>')
    condition = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.defaultCondition">', right='</li>')
    df = pd.DataFrame({
        'distance': dist,
        'race type': racetype,
        'race class': raceclass,
        'surface name': surface,
        'default condition': condition,
    })
    print(df)
    # df.to_csv('./details.csv')
details()

def results():
    with open('results.txt', 'r') as f:
        html = f.read()
    number = find_value_in_html(html, left='runner\.bettingInterestNumber" style="color: rgb\(.{1,20}\)\;">', right='</span></div>')
    name = find_value_in_html(html, left='ng-bind="runner.runnerName">', right='</strong></td>', width=50)
    win = pad_or_trunc(find_value_in_html(html, left='winPayoff\)">\$', right='</td>'), len(number))
    place = pad_or_trunc(find_value_in_html(html, left='placePayoff\)">\$', right='</td>'), len(number))
    show = pad_or_trunc(find_value_in_html(html, left='showPayoff\)">\$', right='</td>'), len(number))
    df = pd.DataFrame({
        'ranking': [_ for _ in range(1, len(number) + 1)],
        'number': number,
        'name': name,
        'win': win,
        'place': place,
        'show': show
    })
    print(df)
    df.to_csv('./results.csv')

def race_card_left():
    with open('summ.txt', 'r') as f:
        html = f.read()

    scratched = find_scratched(html, query='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">')

    number = find_value_in_html(html, left='<span class="horse-number-label" ng-style="\{.{1,20}: runner.numberColor\}" style="color: rgb(.{1,20})\;">', right='</span></div></td>')
    runner_odds = find_value_in_html(html, left='<strong ng-if="!runner.scratched" class="race-current-odds.{0,20}" ng-class="\{.{1,20} : runner.favorite === true\}">', right='</strong>')
    race_morning_odds = find_value_in_html(html, left='<span ng-if="!runner\.scratched" class="race-morning-odds">', right='</span>')
    name = find_value_in_html(html, left='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">', right='</strong>', width=50)
    age = find_value_in_html(html, left='<span qa-label="age">', right='</span>')
    gender = find_value_in_html(html, left='<span qa-label="gender">', right='</span>')
    sire_dam = find_value_in_html(html, left='<span qa-label="sire-dam">', right='</span>', width=70)
    damsire = find_value_in_html(html, left='<span qa-label="damsire" ng-if="runner\.damSire \&amp\;\&amp\; runner\.damSire !== .{0,5}"><strong>by</strong>', right='</span>', width=50)
    owner_name = find_value_in_html(html, left='<span qa-label="owner-name">', right='</span>', width=70)
    df = pd.DataFrame({
        'number': number,
        'runner odds': apply_scratch(runner_odds, scratched),
        'race morning odds': apply_scratch(race_morning_odds, scratched),
        'name': name,
        'age': age,
        'gender': gender,
        'sire dam': sire_dam,
        'damsire': damsire,
        'owner name': owner_name,
    })
    print(df)
    df.to_csv('./racecard_left.csv')

def race_card_summ():
    with open('summ.txt', 'r') as f:
        html = f.read()
    med_weight = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
    trainer = find_value_in_html(html, left='<strong qa-label="trainer-name">', right='</strong>', width=50)
    jockey = find_value_in_html(html, left='<strong qa-label="jockey-name">', right='</strong>', width=50)
    df = pd.DataFrame({
        'med': [m for i, m in enumerate(med_weight) if i % 2 == 0],
        'trainer': trainer,
        'weight': [m for i, m in enumerate(med_weight) if i % 2 == 1],
        'jockey': jockey,
    })
    print(df)
    df.to_csv('./racecard_summ.csv')

def race_card_snap():
    with open('snap2.txt', 'r') as f:
        html = f.read()
    power_wins_daysoff = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
    df = pd.DataFrame({
        'power rating': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 0],
        'wins/starts': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 1],
        'days off': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 2],
    })
    print(df)
    # df.to_csv('./racecard_snap.csv')

def race_card_spee():
    with open('spee.txt', 'r') as f:
        html = f.read()
    as_ad_hs_ac_lc = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
    df = pd.DataFrame({
        'avg speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 0],
        'avg distance': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 1],
        'high speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 2],
        'avg class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 3],
        'last class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 4],
    })
    print(df)
    # df.to_csv('./racecard_spee.csv')

def race_card_pace():
    with open('pace.txt', 'r') as f:
        html = f.read()
    races_early_mid_fin = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
    df = pd.DataFrame({
        'num races': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 0],
        'early': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 1],
        'middle': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 2],
        'finish': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 3],
    })
    print(df)
    # df.to_csv('./racecard_pace.csv')

def race_card_jock():
    with open('jock.txt', 'r') as f:
        html = f.read()
    starts_1_2_3 = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
    df = pd.DataFrame({
        'starts': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 0],
        '1st': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 1],
        '2nd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 2],
        '3rd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 3],
    })
    print(df)
    # df.to_csv('./racecard_jock.csv')

def probables():
    with open('probables.txt', 'r') as f:
        html = f.read()
    probables = find_value_in_html(html, left='<span ng-bind="betCombo.payout">', right='</span>')
    length = int(len(probables) ** 0.5)
    df = pd.DataFrame({
        str(l+1): [r for i, r in enumerate(probables) if i % length == l] for l in range(length)
    })
    print(df)
    # df.to_csv('./probables.csv')

# def willpays():
#     with open('willpays.txt', 'r') as f:
#         html = f.read()
#     wps = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>')
#     df = pd.DataFrame({
#         str(l+1): [r for i, r in enumerate(wps) if i % length == l] for l in range(length)
#     })
#     print(df)
#     # df.to_csv('./willpays.csv')

def pools():
    with open('pools.txt', 'r') as f:
        html = f.read()
    win = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.winPayoff != undefined" ng-bind="runners\.winPayoff">\$', right='</span>')
    place = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.placePayoff != undefined" ng-bind="runners\.placePayoff">\$', right='</span>')
    show = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>')
    df = pd.DataFrame({
        'win': win,
        'place': place,
        'show': show
    })
    print(df)
    # df.to_csv('./pools.csv')
