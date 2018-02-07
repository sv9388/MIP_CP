import pandas as pd
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
            employees[(i, j)] = solver.IntVar(0, tdf.shape[0], "employees(%i,%i)" % (i, j))
            employees_flat.append(employees[(i, j)])
    print("Variables Count = ", len(employees_flat))
    print(arr)
    for i in range(len(arr)):
        solver.Add(solver.AllDifferent([employees[(i, j)] for j in range(arr[i])]))
    for i in range(len(arr)):
        pass
    db = solver.Phase(employees_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
    solution = solver.Assignment()
    solution.Add(employees_flat)
    collector = solver.FirstSolutionCollector(solution)
    print("Solving", solver, solution)
    solver.Solve(db, [collector])
    print("Solutions found:", collector.SolutionCount())
    print("Time:", solver.WallTime(), "ms")
    print()
    for sol in range(collector.SolutionCount()):
        print("Solution number" , sol, '\n')
        for i in range(len(arr)):
            for j in range(arr[i]):
                print(collector.Value(sol, employees[i][j]))

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  sdf['section0'] = 0
  scolumns = ['section1', 'section2', 'section3', 'section4', 'section5']
  h = 9.5
  get_optimized_answer(sdf.loc[sdf.time == h][scolumns].as_matrix()[0], edf[(edf.preferredstart <= h) & ( h <= edf.preferredend)])

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
