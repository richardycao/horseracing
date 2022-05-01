
Step 1: Create raw data.
Run `python3 create_raw_data.py raw_data.csv 2022-03-15 2022-03-22 rank`. args: output_file, start_date, end_date (start and end dates are inclusive), mode (1v1 or rank)
Or to update raw data, run `python3 update_raw_data.py raw_data_2.csv 2022-03-15 2022-03-15`

Step 2: Clean data into X and y.
Run `python3 create_train_data.py raw_data.csv X.csv y.csv avgs.csv rank`. args: input_file, X csv, y csv, output averages file, mode (1v1 or rank)

Step 3: Train a model on the training data.
Run `python3 create_model.py X5.csv y5.csv lgb5.pkl`. args: X csv, y csv, output model file.

Step 4: Use the model to predict winners of individuals races.
Run `python3 predict_races.py bayes 2022-03-15 2022-04-02 avgs5.csv obs_bayes2_m15a02.csv bayes`. args: model file, start_date, end_date (start and end dates are inclusive), averages file, observations file, mode (1v1, rank, bayes, bayes-hist, random)

Other tools:
Run `python3 estimate_takeouts.py estimates.csv 2022-03-15 2022-03-26` to get takeout estimates at each park.
**(BROKEN)** Run `python3 estimate_odds_rank_winrates.py odds_ranks.csv 2022-03-15 2022-03-26 daily` to get, for h horses in a race, the winrate of the horse with the nth-lowest odds. args: output file, start, end, mode (daily, hist)

==========

Pools increase by 10x in the last minute of betting. I need to measure the changes in pool as it approaches expiration. The website updates the pools every ~20 seconds.
- Or I need to time the bet very precisely. But bet size depends on pool size.
- I need to predict where the pools will end up.

DRF (https://www.drf.com/live_odds/winodds/track/AQU/USA/7/D) has fast load times. It's much better for quick gathering of data than TVG.
- here's the GET url for live pools and odds: https://www.drf.com/liveOdds/tracksPoolDetails/currentRace/8/trackId/AQU/country/USA/dayEvening/D/date/4-10-2022


==========

*** I need to do cross-validation on sims and get the average returns ***
*** Consider having a separate model for each number of horses ***
- The model for strictly 8 horses has positive return: 1%.

* create a row for each race, with each race containing 6 to 9 horses.
* send that to colab.
* think about how to standardize each feature in a row.
* within colab, calculate the standardized global averages for each per-horse feature.
* for each race, fill in empties with either the race average, or if all are missing, the global average.
* create duplicate data using the existing code.

found an issue with b_star(). I was taking max(the 2 roots), instead of min(all roots > 0).

found that the odds threshold for long-term profit is implict if b_i > 0. It's still useful though because I can apply a multiplier to account for errors in estimating b_i.

training an MLP on more features didn't help. Is there a way to optimize for max gains, instead of correct p_i's?
- turns out lower val_loss doesn't correlate with better returns.

If I bet q percentage of my money each bet, what odds do I have to have to breakeven?
- This is different from betting a fixed amount each time.

==========

Found a closed form solution for optimal bet size.

Found the threshold at which I will breakeven on a bet. if (odds_i > 1/p_i - 1)

I know my probabilities (p_i's) are wrong because I'm winning a lot less than my probabilities indicate.

Need to put a cap on the amount of money I bet on a race, depending on p_i and odds_i.

KL-divergence might be better than cross-entropy for loss function.

Try using features that are time-independent (not odds, not pools)

==========

*** If the return graph doesn't converge with the expected return graph, then my pi's are off. ***

Most races have 6 to 10 horses. I want to train separate models for each number of horses. Use that to estimate the pi's. Start with 8. Order 8->7->6->9->10.

Is there a way to find the expected number of losses before a win? It depends on what bets I make, which depends on pi's. So I shouldn't prioritize this until I'm confident in my pi's.

Should I focus on place/show bets? I need to visualize how much money is available in each category.

==========

I plotted the distribution of pool_size across 5k races and it comes out to be roughly lognormal. For historical data, since pool size is missing, I can generate a pool size from a lognormal distribution and run many simulations to see if I'm consistently profitable.

Plot my expected returns to see if it aligns with my actual returns.
- aligns fairly well.
Visualize the times that the bets were made to see if I can be awake at those times.
- they're all over the place.

Understand how the pools move near race closing time. Currently, I'm using the end state of the pools. If there's someone who jumps in faster than me, then my bets will be suboptimal.
- Even if there is someone faster than me, there are still inefficiencies that they left out.
- What percentage of the pool is added in the last 1 minute before close? If it's small, then I can be confident in my calculations.

For bayes-hist prediction, combine joint horses into 1 horse. Otherwise it messes up the rest of the odds. What if I don't divide pool_frac by sum of pool instead?

I want to see how close my estimate of payout is to the actual payout.

gradient descent parameters were bad - that's why I kept getting pEr > 1. I set the learning rate to 10, which is decent. I set the precision to 0.01, so it stops later.
- One problem was that GD was exiting too early. I noticed that the bet size was always smaller than the optimal b on the graph.
- Is it bad if I stop early? I get more pEr.
- It used to be lr=1, precision=1. Why did that work better?

What's my expected number of losses until I win 1? What my expected cash loss before I win 1? I need to return to make up for that loss.
- The problem is that I lose too much before I win 1. If bet on place/show, I'll lose less before I win something.
- What percent of races have place and/or show?

==========

The Bayes model is essentially a machine learning model that predicts the probability of a horse winning the race, given 2 features, num_horses and odds_rank. I think all of the features need to be related to the other horses in the race. Rank of avg speed, rank of highest speed, etc.
- Use a bunch of features to predict the probability of a horse winning the race. Do this for every horse. Softmax those values to get my estimates of p for each horse.
- This didn't work. The problem is that it's not optimizing a distribution. It's optimizing to find individual probabilities and then I put them together into a distribution. A model that estimates the distribution itself would be better.

*** I don't need to login to scrape historical data ***
Try getting some imperfect data. The thing I lack most is data. Fortunately, all I need to calculate expected return, r_i, is s, omega, h_i, b_i, and p_i. s is known. I can estimate omega and h_i that roughly fits the odds by using the winning amounts in the results. I can get p from the odds rankings in the results. Using that I can find b_i and r_i. It's not perfect but it's a lot of data.
- It's easier to click a race track in the dropdown than it is to click a certain calendar day.

Autoencoders naturally estimate a distribution. I can account for the variable number of horses by using a max number of horses - only use races with 10 or fewer horses.
- Check the simulation to see how many horses are in the races I predicted on. THe highest is 8. So it makes sense to limit the number of horses to 10. The probabilities estimates will get too noisy with a lot of horses anyway.
- Bayesian deep learning: https://jorisbaan.nl/2021/03/02/introduction-to-bayesian-deep-learning.html#:~:text=A%20Bayesian%20Neural%20Network%20(BNN,even%20more%20difficult%20than%20usual.
- VAEs: https://towardsdatascience.com/understanding-variational-autoencoders-vaes-f70510919f73

Include up to 10 horses in a dataset. Toss the races with >10 horses. Train a supervised learning model, where each sample contains all 10 horses. 1 race may produce samples that contain all combinations of the 10 horses - 10! horses. The output of the model should be probabilities of winning for each horse. I can use softmax here, since it's part of the optimization that the model is doing.

==========

 *** it's possible that binary classification models (rf, lgb) can't come close to using an empircal distribution (bayes). I might need to use a different strategy to estimate the `probability of 1st place, given horse_pool/total_pool`. Combining results of binary classification models into probabilities is an unnatural approach, and gives inncorrect probabilities. ***
 - even though the winrate is high, the expected return is negative because the probabilities are calculated incorrectly.
 - maybe instead of predicting the winners of 1v1s, I can predict the chance of winning for a single horse, given it's pool_frac.
 - also include number of horses in the race into the data.
 - I can extend the bayes model by using num_horses -> pool_frac (maybe).
 - The Bayes model is essentially a machine learning model that predicts the probability of a horse winning the race, given 2 features, num_horses and odds_rank. I think all of the features need to be related to the other horses in the race. Rank of avg speed, rank of highest speed, etc.

a higher model 1v1 winrate doesn't correlate with better simulation results.

use a different odds_rank distribution based on number of horses.
include number of horses in the dataset.

Er and Dr calculation may be wrong. Fixed - removed the +1 from Er calculation.

include horse_pool/total_pool in the dataset. maybe for place and show too.

==========

include odds rank in the dataset.

if a column is missing a significant amount of data, remove all samples that are missing data for that column. alternative - don't include races that are missing entire columns.

==========

can I make profit at takeout of 15%? I can include park name in the simulation data. then only make bets on races at certain parks.
can I estimate takeout rates from results.csv and pools.csv? try that.

Find some parks with low rates.

List of takeout rates at different parks from 2017: http://www.horseplayersassociation.org/2017Sortable.html

I set the takeout to 0% and I actual made money in simulation. So now I know it's the takeout that's making it really hard to profit.

I tried using natural distribution of winner by nth-highest-odds for p. e.g. lowest odds wins 32% of the time, 2nd lower wins 28%, etc. p = 0.32,0.28,...hardcoded. It performed better than the model, which means it probably estimated probabilities of winning (p) better than the model did.

*** Don't use softmax for scoring ***
Softmax is assigning some horses 50 to 90% chances of winning, which is unrealistic. On average, the favorite horse wins 33% of the time. It's the horse that wins the most too.

The components are: ranking or horse probabilities

My ranking algorithm doesn't work - it doesn't give the correct percentages for winrate of each horse. How close is it to the actual ranks anyway?

if a column is missing a significant amount of data, remove all samples that are missing data for that column. alternative - don't include races that are missing entire columns.

try predicting place/score instead of win.

try include 3 horses in each sample, instead of 2.

ideas from https://www.youtube.com/watch?v=pmxBDuju3GU:
- use -1 to 1 instead of 0/1.

instead of choosing the horse with the highest expected return, go back to choosing the hose that I think will win, but modify the probability calculation estimate p better.

try training a separate model for each number of horses.

==========

What I know at each step:
1. Create raw data - I either use all races (train), or only races with all results (test).
2. Clean data - don't use odds, remove date, normalize a bunch of stuff.
3. Train model - rf, lgbm, or nn. rf has been best empircally so far.
4. Predictions - use small test sets in the beginning for fast testing. increase the size to gain confidence in the results. for winrate, scoring can be by prediction or probability. for return, scoring may be MSE.

at each step, I don't just want to take the horse that I think will win. I want to take the horse that I think has the highest return. This could mean taking horses with lower confidence score because they have higher odds. I should record the ranking of all horses at the end, not just the winner.

account for pools_i
include horse_number in obs. I'll be comparing scores (includes 1A) with pools (excludes 1A) so I need to align them somehow.

don't use softmax (?)

==========

try additive probabilities for scoring=1.
try only using races that show full results.
maybe add odds back into the dataset?
try predicting for place or show instead. there's a higher chance of an underdog to make it.
remove date from training data. I don't have a year's worth of data for it to be relevant.
test on a smaller set (1 day) for faster testing.

I need underdog winners to matter more in training. The model needs to be about how much expected return I get, not just winrate. 

*** Do not shuffle data during training ***
Validation data needs to come from different races than training data comes from.
*** Do not include odds in the training data ***
If the goal is to predict wins, then low odds will be more likely to win. But low odds give low returns.

remove weak features from the model?
remove bet limit?

- include date and time into observations from the title of the race
- include pools into raw_data.csv from pool.csv
- account for pool size when betting - I can drastically alter the odds by betting a lot. include pool size in observations.
- find the distribution of pool sizes. I need to know which races I can bet more on.

number 1 priority:
- better data preprocessing.
- optimize the model since it's not profitable yet.
- standardize the units of each column.
- RankNet: https://towardsdatascience.com/learning-to-rank-for-information-retrieval-a-deep-dive-into-ranknet-200e799b52f4
- LambdaRank: 

TODO:
- try training on place or show instead.
- returns are multiplicative so they are calculated wrong in evaluate_observation.ipynb.
- look into crowdsourced league worlds rankings. softmax: https://www.pro-football-reference.com/blog/indexa828.html?p=171

X2 - contains odds and some normalized features
X3 - removes odds
X4 - includes odds again and removes dates

===================

Pipeline stuff for later:

set up efficient train-val.
1. train a neural network on 1, val on 2. train on 1 and 2 (continue training the previous model on 2), val on 3. continue train on 3, val on 4.
2. track the f1 score after each step.

inference:
`create_df.py` is good for creating a mixed dataset for training. But it's not good if I want to do inference per-race. Inference should draw directly from `scrape/results`. It creates a new df of pairs for each file, preprocesses it normally without shuffle, then runs inference. At the end, it matches up the winners between horses and figures out the rankings.

training:
If I want to update the model when new data arrives, I can't be putting everything into a single dataset with `create_df.py`. I need something that will create a lightweight dataset that I can feed into a pipeline to trigger a training session. The pipeline should operate by-race. Whenever new race data arrives for training, the model updates on that race only. Whenever new race data arrives for inference, the inference should only be performed on that race.

have airflow trigger a training session every 12 hours, if there is new data.
use a deep learning model instead so I can save checkpoints and update it every training session.

The end goal is:
I manually run the data gathering script each day. I manually upload the data somewhere.
I can call an api and give it some data and it will tell me the ordering of horses and the confidence.
