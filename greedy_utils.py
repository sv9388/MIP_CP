import pandas as pd, time
from ortools.constraint_solver import pywrapcp

MAX_BREAKS = 2
BREAK_UNIT = 6

def get_df(sf, ef):
  section_df = pd.read_csv(sf)
  employees_df = pd.read_csv(ef)
  return section_df, employees_df

# meet all requirements per section at minimum labour-hours

_ = """employees = N, sections = 6 (5 + 1)
assign different employees to sections  (dynamic sized array)
employees start >= current hour employees end <= current hour
section id in certified sections array #TODO"""
def get_optimized_answer(arr, tdf):
    solver = pywrapcp.Solver("schedule_sections")
    employees = {}
    employees_flat = []
    for i in range(len(arr)):
        for j in range(arr[i]):
            employees[(i, j)] = solver.IntVar(1,1+ tdf.shape[0], "employees(%i,%i)" % (i, j))
            employees_flat.append(employees[(i, j)])
    for i in range(len(arr)):
        solver.Add(solver.AllDifferent(employees_flat)) #for j in range(arr[i])]))
    db = solver.Phase(employees_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_RANDOM_VALUE)
    solution = solver.Assignment()
    solution.Add(employees_flat)
    collector = solver.FirstSolutionCollector(solution)
    solver.Solve(db, [collector])
    op = []
    for sol in range(collector.SolutionCount()):
        op = [[ collector.Value(sol, employees[(i,j)]) for j in range(arr[i])] for i in range(len(arr))]
    return op

def main(sf, ef):
  start = time.time()
  print("Started at", start)
  sdf, edf = get_df(sf, ef)
  sdf['section0'] = 0
  scolumns = ['section1', 'section2', 'section3', 'section4', 'section5']
  row_section = lambda i : [int(x) for x in sdf.loc[i][scolumns].as_matrix().tolist()]

  op = []
  strict_timings = []
  for i in range(sdf.shape[0]):
    op.append(("PREFER", row_section(i), get_optimized_answer(row_section(i), edf[(edf.preferredstart <= sdf.loc[i].time) & ( sdf.loc[i].time <= edf.preferredend)])))
  processed = time.time()
  print("Preferred Solution found in ", processed - start, "seconds")
  for i in range(len(op)):
    if len(op[i][-1]) == 0:
      strict_timings.append(i)
  for i in strict_timings:
    op[i] = ("STRICT", row_section(i), get_optimized_answer(row_section(i), edf[(edf.earlieststart<= sdf.loc[i].time) & (sdf.loc[i].time <= edf.latestend)]))
  print("Strict solution found in", time.time() - start, "seconds")
  for i in range(len(op)):
    if len(op[i][-1]) == 0:
      op[i] = ("NOSOL", row_section(i), None)

  for i in range(len(op)):
    print(i, ": ", op[i])
  print("Total Time", time.time() - start, "seconds")

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
