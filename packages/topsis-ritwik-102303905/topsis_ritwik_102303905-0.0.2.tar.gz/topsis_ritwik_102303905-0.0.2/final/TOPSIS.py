import sys
import numpy as np

def read_csv(input_file):
  try:
    with open(input_file, "r") as f:
      lines = f.readlines()
  except FileNotFoundError:
    print("Input file not found")
    sys.exit(1)

  header = lines[0].strip().split(",")
  rows = [line.strip().split(",") for line in lines[1:]]
  return header, rows

def write_csv(input_file, header, data):
  with open(input_file, "w") as f:
    f.write(",".join(header) + "\n")
    for row in data:
      f.write(",".join(str(x) for x in row) + "\n")

def topsis(data, weights, impacts):
  n = len(data)
  m = len(data[0])

  # normalize
  norm = [[0 for j in range(m)] for i in range(n)]

  for j in range(m):
    col_sum_sq = 0
    for i in range(n):
      col_sum_sq += data[i][j] ** 2

    for i in range(n):
      norm[i][j] = data[i][j] / (col_sum_sq ** 0.5)

  # apply weights
  weighted = [[0 for j in range(m)] for i in range(n)]

  for i in range(n):
    for j in range(m):
      weighted[i][j] = norm[i][j] * weights[j]

  # calculate ideal best & worst
  ideal_best = [0 for j in range(m)]
  ideal_worst = [0 for j in range(m)]

  for j in range(m):
    column = [weighted[i][j] for i in range(n)]

    if impacts[j] == "+":
      ideal_best[j] = max(column)
      ideal_worst[j] = min(column)

    elif impacts[j] == "-":
      ideal_best[j] = min(column)
      ideal_worst[j] = max(column)

  # calculate distances
  dist_best = [0 for i in range(n)]
  dist_worst = [0 for i in range(n)]

  for i in range(n):
    sum_sq_best = 0
    sum_sq_worst = 0

    for j in range(m):
      sum_sq_best += (weighted[i][j] - ideal_best[j]) ** 2
      sum_sq_worst += (weighted[i][j] - ideal_worst[j]) ** 2

    dist_best[i] = sum_sq_best ** 0.5
    dist_worst[i] = sum_sq_worst ** 0.5

  # calculate score
  scores = [0 for i in range(n)]
  for i in range(n):
    scores[i] = dist_worst[i] / (dist_best[i] + dist_worst[i])

  return scores

if len(sys.argv) != 5:
  print("Enter prompt in format: python <topsis.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
  sys.exit(1)

input_file = sys.argv[1]
weights_string = sys.argv[2]
impacts_string = sys.argv[3]
output_file = sys.argv[4]

if "," not in weights_string or "," not in impacts_string:
  print("Weights and impacts must be separated by commas")
  sys.exit(1)

try:
  weights = [float(w) for w in weights_string.split(",")]
except ValueError:
  print("Weights must be floating values")
  sys.exit(1)

impacts = impacts_string.split(",")

for imp in impacts:
  if imp not in ["+", "-"]:
    print("Impacts must be + or -")
    sys.exit(1)

header, rows = read_csv(input_file)

if len(header) < 3:
  print("Input file must have minimum three columns")
  sys.exit(1)

try:
  data = []
  for row in rows:
    data.append([float(x) for x in row[1:]])
    
except ValueError:
  print("Input file must contain numeric values second column onwards")
  sys.exit(1)

m = len(data[0])

if len(weights) != m or len(impacts) != m:
  print("Number of weights, impacts, and input columns must be same")
  sys.exit(1)

# run TOPSIS
scores = topsis(data, weights, impacts)

ranked_indices = np.argsort(scores)[::-1]
ranks = np.zeros(len(scores), dtype=int)

for rank, i in enumerate(ranked_indices, start=1):
  ranks[i] = rank

# create output file
output_header = header + ["TOPSIS Score", "Rank"]
output_data = []

for i in range(len(rows)):
  output_data.append(rows[i] + [round(scores[i], 6), ranks[i]])

write_csv(output_file, output_header, output_data)

print("TOPSIS completed")
print("Output saved to:", output_file)