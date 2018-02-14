import pandas as pd, numpy as np, time
from ortools.constraint_solver import pywrapcp

MAX_BREAKS = 2
BREAK_UNIT = 4
HOUR_UNIT = 2 # How many hour slices make an hour?

def get_df(sf, ef):
  section_df = pd.read_csv(sf)
  employees_df = pd.read_csv(ef)
  return section_df, employees_df

def get_optimized_answer(arr, tdf, break_emps):
  print("Break valid employees", break_emps)
  solver = pywrapcp.Solver("schedule_sections")
  employees = {}
  employees_flat = []
  for i in range(len(arr)):
    for j in range(arr[i]):
      employees[(i, j)] = solver.IntVar(0, tdf.shape[0], "employees(%i,%i)" % (i, j))
      employees_flat.append(employees[(i, j)])
  # At a given timeslice, different employees should be allocated. at each section , except 0 (Break)
  for i in range(len(arr)):
    solver.Add(solver.AllDifferent([employees[(i, j)] for i in range(1, len(arr)) for j in range(arr[i])])) #for j in range(arr[i])]))
  _ = """# At a given timeslice, section 0 can have only employees from break_emps
  if len(break_emps)>0:):
      pass #solver.Add(solver.IsMemberVar(employees[(0, j)], break_emps))
  else:
    solver.Add(solver.Sum([ employees[(0, i)] for i in range(arr[0]) ]) == 0)
  # Optimizer """
  db = solver.Phase(employees_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_RANDOM_VALUE)
  solution = solver.Assignment()
  solution.Add(employees_flat)
  collector = solver.FirstSolutionCollector(solution)
  solver.Solve(db, [collector])
  op = []
  for sol in range(collector.SolutionCount()):
    op = [[ collector.Value(sol, employees[(i,j)]) for j in range(arr[i])] for i in range(len(arr))]
  print("Output", op)
  return op

scolumns = ['section1', 'section2', 'section3', 'section4', 'section5']
def ans_row(sdf, edf, ecols):
  secol, eecol = ecols
  op = []
  row_section = lambda i : [int(x) for x in sdf.loc[i][scolumns].as_matrix().tolist()]
  for i in range(sdf.shape[0]):
    r = row_section(i)
    arr = list(edf[(edf[secol] * HOUR_UNIT + BREAK_UNIT <= i) & (i <= edf[eecol] * HOUR_UNIT - BREAK_UNIT)].index)
    ans = get_optimized_answer(r, edf[(edf[secol]<= sdf.loc[i].time) & (sdf.loc[i].time <= edf[eecol])], arr)
    op.append(ans)
  return op

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  op = ans_row(sdf, edf, ["preferredstart", "preferredend"])
  for x in op:
    print(x)
  _ = """ strict_timings = []
  for i in range(len(op)):
    if len(op[i]) == 0:
      strict_timings.append(i)
  for i in strict_timings:
    op[i] = ("STRICT", row_section(i), get_optimized_answer(row_section(i), edf[(edf.earlieststart<= sdf.loc[i].time) & (sdf.loc[i].time <= edf.latestend)]))
    print("Strict solution found in", time.time() - start, "seconds")
  for i in range(len(op)):
    if len(op[i][-1]) == 0:
      op[i] = ("NOSOL", row_section(i), None)
  for x in op:
  print(x)
  arrop = [[-1 for i in range(sdf.shape[0])]for j in range(edf.shape[0])]
  for h in range(len(op)): 
  if op[h][0] == "NOSOL":
    continue
  d = op[h][2]
  print(d)
  for s in range(5):
    for e in d[s]:
    print(len(arrop), len(arrop[0]), e, h)
    arrop[e-1][h] = s
  op = pd.DataFrame(arrop)
  op.to_csv("./op.csv")"""

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
