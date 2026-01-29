# Imports
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import argparse
import sys

# Conversion of weights and impacts into list
def parse_list(arg):
  if "," not in arg:
      print("Weights and impacts must be separated by comma (,)")
      sys.exit(1)
  return [x.strip() for x in arg.split(",")]

# Saving Parameters from command line arguments
if len(sys.argv) != 5:
  print("Invalid number of arguments!")
  print('Command: python app.py data.csv "0.25,0.25,0.25,0.25" "-,+,+,+" output.csv')
  sys.exit(1)

input_file = sys.argv[1]
weights_arg = sys.argv[2]
impacts_arg = sys.argv[3]
output_file = sys.argv[4]

# Reading of data from input file
try:
  data = pd.read_csv(input_file)
except FileNotFoundError:
  print("File not found!", input_file)
  sys.exit(1)
except Exception as e:
  print("Error: ", e)
  sys.exit(1)

if data.shape[1] < 3:
  print("Input file must contain at least 3 columns")
  sys.exit(1)

# Validation for data, weights and impacts
data = data.drop(data.columns[0], axis = 1)
categorical_cols = data.select_dtypes(include = ['object', 'category']).columns

if len(categorical_cols) > 0:
  print("Data File contains non numeric column")
  sys.exit(1)
impacts = parse_list(impacts_arg)

try:
  weights = list(map(float, parse_list(weights_arg)))
except:
  print("Weights must be numeric values.")
  sys.exit(1)

if not all(i in ["+", "-"] for i in impacts):
  print("Impacts must be only + or -")
  sys.exit(1)

if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
  print("Number of weights, impacts must be equal to number of columns.")
  sys.exit(1)

print(data, "\n\n", "weights:", weights, "\n\n", "impacts:", impacts, "\n\n")

# Calculate root of sum of square
data_new = data.copy()
data_new.columns = range(len(data_new.columns))
squared_sum = data_new ** 2
root_squared_sum = np.sqrt(squared_sum.sum())
print(root_squared_sum, "\n\n")

# Normalizing Value
data_new = data_new / root_squared_sum
print(data_new, "\n\n")

# Assigning Weights
data_new = data_new * weights
print(data_new, "\n\n")

# Calculating ideal value using impacts
vj_max = pd.Series()
vj_min = pd.Series()

for i in range(len(impacts)):
  if impacts[i] == "+":
    vj_max[i] = data_new[i].max()
    vj_min[i] = data_new[i].min()
  else:
    vj_max[i] = data_new[i].min()
    vj_min[i] = data_new[i].max()

print(vj_max, "\n\n", vj_min, "\n\n")

# Calculating euclidean distance
st_max = np.sqrt(((data_new - vj_max) ** 2).sum(axis = 1))
st_min = np.sqrt(((data_new - vj_min) ** 2).sum(axis = 1))
print(st_max, "\n\n", st_min, "\n\n")

# Calculating Performance Score
p = st_min / (st_min + st_max)
print(p, "\n\n")

# Ranking based on Performance Score
rank = p.rank(ascending = False).astype(int)
print(rank, "\n\n")

# Joining performance score and rank in original data
data["Topsis Score"] = p
data["Rank"] = rank
print(data, "\n\n")

# Saving final data to output file
try:
  data.to_csv(output_file, index = False)
  print("TOPSIS completed successfully!")
  print("Output saved to:", output_file)
except Exception as e:
  print("Error saving output file:", e)