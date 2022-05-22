import json
import pandas as pd
import sys
from collections import defaultdict
import choix
from tqdm import tqdm
import datetime as dt

def extract_dict(dict_str):
    try:
        return json.loads(dict_str)
    except:
        return None

def get_uniques(df, bi_feature, num_race_features, threshold=1):
    uniques = defaultdict(lambda: 0)
    for r in range(df.shape[0]):
        for c in range(num_race_features,df.shape[1]):
            d = extract_dict(df.iloc[r,c])
            if d == None:
                continue
            uniques[d[bi_feature]] += 1
    threshold_uniques = {k:v for k,v in uniques.items() if v >= threshold}
    return {k: v for k, v in sorted(threshold_uniques.items(), key=lambda x: -x[1])}

def get_ratings2(df, bi_feature, num_race_features, min_required_uniques=1, uniques_upper_cutoff=None):
  print(f'Getting ratings for {bi_feature}')
  print('  Getting uniques.')
  uniques = get_uniques(df, bi_feature, num_race_features, min_required_uniques)
  print(f'    Uniques: {len(uniques)}.')

  # map categories to numbers
  cat_num = { k: i for i, k in enumerate(uniques.keys()) }
  num_cat = { i: k for i, k in enumerate(uniques.keys()) }

  # go through each race and get all the comparisons from the results
  print('  Creating win-lose graph.')
  win_lose = { v: [] for v in cat_num.values() }
  lose_win = { v: [] for v in cat_num.values() }
  occurrences = { k: 0 for k in uniques.keys() }
  for r in tqdm(range(df.shape[0])):
    ds = [extract_dict(df.iloc[r,c]) for c in range(num_race_features, df.shape[1])]
    for i in range(len(ds)):
      if ds[i] == None:
        continue
      bif_i = ds[i][bi_feature]
      if bif_i not in cat_num:
        continue
      if uniques_upper_cutoff != None and occurrences[bif_i] >= uniques_upper_cutoff:
        continue
      occurrences[bif_i] += 1

      for j in range(i+1, len(ds)):
        if ds[j] == None:
          continue
        bif_j = ds[j][bi_feature]
        if bif_j not in cat_num:
          continue
        if (ds[i]['finishPosition'] < ds[j]['finishPosition']) or (not pd.isna(ds[i]['finishPosition']) and pd.isna(ds[j]['finishPosition'])):
          win_lose[cat_num[bif_i]].append(cat_num[bif_j])
          lose_win[cat_num[bif_j]].append(cat_num[bif_i])
        elif (ds[i]['finishPosition'] > ds[j]['finishPosition']) or (pd.isna(ds[i]['finishPosition']) and not pd.isna(ds[j]['finishPosition'])):
          win_lose[cat_num[bif_j]].append(cat_num[bif_i])
          lose_win[cat_num[bif_i]].append(cat_num[bif_j])

  print('  Creating win-lose pairs.')
  pairs = []
  for k,v in tqdm(win_lose.items()):
    for loser in v:
      pairs.append((k, loser))
  
  print(f'    Number of pairs: {len(pairs)}')

  print('  Calculating ratings.')
  n_items = len(win_lose)
  del uniques, cat_num, win_lose, lose_win
  params = choix.ilsr_pairwise(n_items, pairs, alpha=0.01)
  return { num_cat[i]: params[i] for i in range(len(params)) }

def main(horseracing_path, feature_name):
    num_race_features = 5

    data12 = pd.read_csv(horseracing_path + 'hist_data_upto12_includemissing.csv', header=None)
    data12.iloc[:,4] = data12.iloc[:,4].apply(lambda x: dt.datetime.strptime(x.split('/')[3], "%Y-%m-%d"))
    recent_data = data12.sort_values([4], ascending=False)
    print(data12.shape)
    del data12

    horseName_ratings = get_ratings2(recent_data, feature_name, num_race_features, 
                                 min_required_uniques=5, uniques_upper_cutoff=1)
    with open(horseracing_path + f"{feature_name}_ratings12_im_v2.json", "w") as f:
        json.dump(horseName_ratings, f)

if __name__ == "__main__":
    args = sys.argv[1:]
    # path, feature_name
    main(args[0], args[1])