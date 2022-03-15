import re

def find_value(html, left, right, width=50):
    return [[html[i.end():i.end()+j.start()] for j in re.finditer(right, html[i.end(): i.end() + width])][0] for i in re.finditer(left, html)]

# results
# with open('results.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='runner\.bettingInterestNumber" style="color: rgb\(.{1,20}\)\;">', right='</span></div>'))
# print(find_value(html, left='ng-bind="runner.runnerName">', right='</strong></td>'))
# print(find_value(html, left='winPayoff\)">\$', right='</td>'))
# print(find_value(html, left='placePayoff\)">\$', right='</td>'))
# print(find_value(html, left='showPayoff\)">\$', right='</td>'))
# print()

# race card - left side
# with open('summ.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<span class="horse-number-label" ng-style="\{.{1,20}: runner.numberColor\}" style="color: rgb(.{1,20})\;">', right='</span></div></td>'))
# # odds might have an issue. it only finds 7, instead of 8 horses.
# print(find_value(html, left='<strong ng-if="!runner.scratched" class="race-current-odds.{0,20}" ng-class="\{.{1,20} : runner.favorite === true\}">', right='</strong>'))
# print(find_value(html, left='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5" qa-label="horse-name">', right='</strong>'))
# print(find_value(html, left='<span qa-label="age">', right='</span>'))
# print(find_value(html, left='<span qa-label="gender">', right='</span>'))
# print(find_value(html, left='<span qa-label="sire-dam">', right='</span>'))
# print(find_value(html, left='<span qa-label="damsire" ng-if="runner\.damSire \&amp\;\&amp\; runner\.damSire !== .{0,5}"><strong>by</strong>', right='</span>'))
# print(find_value(html, left='<span qa-label="owner-name">', right='</span>'))

# race card - summary
# print(find_value(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>'))
# print(find_value(html, left='<strong qa-label="trainer-name">', right='</strong>'))
# print(find_value(html, left='<strong qa-label="jockey-name">', right='</strong>'))

# race card - snapshot
# with open('snap.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>'))

# race card - speed & class
# with open('spee.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>'))

# race card - pace
# with open('pace.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>'))

# race card - jockey/trainer stats
# with open('jock.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>'))

# probables
# with open('probables.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<span ng-bind="betCombo.payout">', right='</span>'))

# will pays
# with open('willpays.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>'))

# pools
# with open('pools.txt', 'r') as f:
#     html = f.read()
# print(find_value(html, left='<span class="amounts text-centered td" ng-if="runners\.winPayoff != undefined" ng-bind="runners\.winPayoff">\$', right='</span>'))
# print(find_value(html, left='<span class="amounts text-centered td" ng-if="runners\.placePayoff != undefined" ng-bind="runners\.placePayoff">\$', right='</span>'))
# print(find_value(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>'))

