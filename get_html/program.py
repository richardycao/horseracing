import utils
from selenium.webdriver.common.by import By
import pandas as pd

def get_details(browser, race_path):
    details = utils.safe_find(browser, By.CLASS_NAME, 'pp-header_race-details_list', num_results=1, retries=3)
    if not details:
        print('Error finding details. Skipping this section for path:', race_path)
        return

    html = details[0].get_attribute('innerHTML')
    dist = utils.find_value_in_html(html, left='<li ng-bind="data.distance">', right='</li>')
    racetype = utils.find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.raceType.Name">', right='</li>')
    raceclass = utils.find_value_in_html(html, left='<span ng-bind="data.currentRace.raceClass">', right='</span>')
    surface = utils.find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.surfaceName">', right='</li>')
    condition = utils.find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.defaultCondition">', right='</li>')
    df = pd.DataFrame({
        'distance': dist,
        'race type': racetype,
        'race class': raceclass,
        'surface name': surface,
        'default condition': condition,
    })
    df.to_csv(f'{race_path}/details.csv')

def get_results(browser, race_path):
    results = utils.safe_find(browser, By.CLASS_NAME, 'table.race-results.no-margin', num_results=1, retries=1)
    if not results:
        print('Error finding results. Skipping this section for path:', race_path)
        return

    html = results[0].get_attribute('innerHTML')
    number = utils.find_value_in_html(html, left='runner\.bettingInterestNumber" style="color: rgb\(.{1,20}\)\;">', right='</span></div>')
    name = utils.find_value_in_html(html, left='ng-bind="runner.runnerName">', right='</strong></td>')
    win = utils.pad_or_trunc_list(utils.find_value_in_html(html, left='winPayoff\)">\$', right='</td>'), len(number))
    place = utils.pad_or_trunc_list(utils.find_value_in_html(html, left='placePayoff\)">\$', right='</td>'), len(number))
    show = utils.pad_or_trunc_list(utils.find_value_in_html(html, left='showPayoff\)">\$', right='</td>'), len(number))
    df = pd.DataFrame({
        'ranking': [_ for _ in range(1, len(number) + 1)],
        'horse number': number,
        'horse name': name,
        'win': win,
        'place': place,
        'show': show
    })
    df.to_csv(f'{race_path}/results.csv')

def get_race_card(browser, race_path):
    tabs = ['Summary', 'Snapshot', 'Speed & Class', 'Pace', 'Jockey/Trainer Stats']

    for i, t in enumerate(tabs):
        tabs = utils.safe_find(browser, By.LINK_TEXT, t, num_results=1, retries=1)
        if not tabs:
            print(f'Error finding element tab {t}. Skipping this section for path:', race_path)
            return
        tabs[0].click()

        tables = utils.safe_find(browser, By.CLASS_NAME, 'race-handicapping-results', num_results=1, retries=1)
        if not tables:
            print(f'Error finding data for tab {t}. Skipping this section for path:', race_path)
            return

        html = tables[0].get_attribute('innerHTML')
        if i == 0:
            scratched = utils.find_scratched(html, query='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">')

            number = utils.find_value_in_html(html, left='<span class="horse-number-label" ng-style="\{.{1,20}: runner.numberColor\}" style="color: rgb(.{1,20})\;">', right='</span></div></td>')
            runner_odds = utils.find_value_in_html(html, left='<strong ng-if="!runner.scratched" class="race-current-odds.{0,20}" ng-class="\{.{1,20} : runner.favorite === true\}">', right='</strong>')
            race_morning_odds = utils.find_value_in_html(html, left='<span ng-if="!runner\.scratched" class="race-morning-odds">', right='</span>')
            name = utils.find_value_in_html(html, left='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">', right='</strong>', width=50)
            age = utils.find_value_in_html(html, left='<span qa-label="age">', right='</span>')
            gender = utils.find_value_in_html(html, left='<span qa-label="gender">', right='</span>')
            sire_dam = utils.find_value_in_html(html, left='<span qa-label="sire-dam">', right='</span>', width=70)

            # damsire and owner name aren't present for japanese races. leave these out for now.
            # damsire = utils.find_value_in_html(html, left='<span qa-label="damsire" ng-if="runner\.damSire \&amp\;\&amp\; runner\.damSire !== .{0,5}"><strong>by</strong>', right='</span>', width=50)
            # owner_name = utils.find_value_in_html(html, left='<span qa-label="owner-name">', right='</span>', width=70)
            df = pd.DataFrame({
                'number': number,
                'runner odds': utils.apply_scratched(runner_odds, scratched),
                'race morning odds': utils.apply_scratched(race_morning_odds, scratched),
                'name': name,
                'age': age,
                'gender': gender,
                'sire dam': sire_dam,
                # 'damsire': damsire,
                # 'owner name': owner_name,
            })
            df.to_csv(f'{race_path}/racecard_left.csv')

            med_weight = utils.find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            trainer = utils.find_value_in_html(html, left='<strong qa-label="trainer-name">', right='</strong>', width=50)
            jockey = utils.find_value_in_html(html, left='<strong qa-label="jockey-name">', right='</strong>', width=50)
            df = pd.DataFrame({
                'med': [m for i, m in enumerate(med_weight) if i % 2 == 0],
                'trainer': trainer,
                'weight': [m for i, m in enumerate(med_weight) if i % 2 == 1],
                'jockey': jockey,
            })
            df.to_csv(f'{race_path}/racecard_summ.csv')
        elif i == 1:
            power_wins_daysoff = utils.find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'power rating': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 0],
                'wins/starts': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 1],
                'days off': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 2],
            })
            df.to_csv(f'{race_path}/racecard_snap.csv')
        elif i == 2:
            as_ad_hs_ac_lc = utils.find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'avg speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 0],
                'avg distance': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 1],
                'high speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 2],
                'avg class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 3],
                'last class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 4],
            })
            df.to_csv(f'{race_path}/racecard_spee.csv')
        elif i == 3:
            races_early_mid_fin = utils.find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'num races': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 0],
                'early': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 1],
                'middle': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 2],
                'finish': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 3],
            })
            df.to_csv(f'{race_path}/racecard_pace.csv')
        elif i == 4:
            starts_1_2_3 = utils.find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'starts': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 0],
                '1st': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 1],
                '2nd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 2],
                '3rd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 3],
            })
            df.to_csv(f'{race_path}/racecard_jock.csv')

# Only works if the default selection is $1 Exacta. Doesn't work for others yet.
def get_probables(browser, race_path):
    probables = utils.safe_find(browser, By.CLASS_NAME, 'scroll-x', num_results=1, retries=1)
    if not probables:
        print('Error finding probables. Skipping this section for path:', race_path)
        return

    html = probables[0].get_attribute('innerHTML')
    probables = utils.find_value_in_html(html, left='<span ng-bind="betCombo.payout">', right='</span>')
    length = int(len(probables) ** 0.5)
    df = pd.DataFrame({
        str(l+1): [r for i, r in enumerate(probables) if i % length == l] for l in range(length)
    })
    df.to_csv(f'{race_path}/probables.csv')

# Doesn't work for now
def get_willpays(browser, race_path):
    willpays = utils.safe_find(browser, By.CLASS_NAME, 'result-runners-table', num_results=1, retries=1)
    if not willpays:
        print('Error finding willpays. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/willpays.txt', 'w') as f:
        f.write(willpays[0].get_attribute('innerHTML'))

def get_pools(browser, race_path):
    pools = utils.safe_find(browser, By.CLASS_NAME, 'result-runners-table.pools-table', num_results=1, retries=1)
    if not pools:
        print('Error finding pools. Skipping this section for path:', race_path)
        return

    html = pools[0].get_attribute('innerHTML')
    win = utils.find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.winPayoff != undefined" ng-bind="runners\.winPayoff">\$', right='</span>')
    place = utils.find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.placePayoff != undefined" ng-bind="runners\.placePayoff">\$', right='</span>')
    show = utils.find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>')
    df = pd.DataFrame({
        'win': win,
        'place': place,
        'show': show
    })
    df.to_csv(f'{race_path}/pools.csv')   

def get_race(browser, race_path):
    get_details(browser, race_path)
    get_results(browser, race_path)
    get_race_card(browser, race_path)
    # get_probables(browser, race_path)
    # get_willpays(browser, race_path)
    get_pools(browser, race_path)