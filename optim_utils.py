import pandas as pd
from ortools.constraint_solver import pywrapcp

def get_df():
  section_df = pd.read_csv('./optimiz_sections.csv')
  employees_df = pd.read_csv('./optimiz_employees.csv')
  return section_df, employees_df

# meet all requirements per section at minimum labour-hours
def get_optimized_answer(sections_df, employees_df):
  #0. Variables
  section_count = 3#6 #5 + 1
  employee_count = employees_df.shape[0]
  hours_count = sections_df.shape[0]
  solver = pywrapcp.Solver("schedule_sections")
  #1. Assign sections to employees.
  sections = {}
  for j in range(employee_count):
    for i in range(hours_count):
      sections[(j, i)] = solver.IntVar(0, section_count - 1, "sections(%i,%i)" % (j, i))
  sections_flat = [sections[(j, i)] for j in range(employee_count) for i in range(hours_count)]
  #2. Assigned to section zero means not working
  #3. 1 employee 1 section at a time.
  #4. Employees work 6 to 8 hours. Doesn't work before start time and doesn't work after end time.
  _ = """for j in range(employee_count):
    pref_start_idx = int(2 * employees_df.loc[j]['Preferred Start of shift']) + 1
    pref_end_idx   = int(2 * employees_df.loc[j]['Preferred end of shift']) + 1
    print(pref_start_idx, pref_end_idx)
    for i in range(pref_start_idx):
      solver.Add(sections[(j, i)] == 0)
    for i in range(pref_end_idx + 1, hours_count):
      solver.Add(sections[(j, i)] == 0)
  #5. Employees work only in certified sections
  for j in range(employee_count):
    certified_sections = employees_df.loc[j]['Section certifications'].split(",")
    certified_sections = [0] + [int(x) for x in certified_sections]
    print(certified_sections)
    for i in range(hours_count):
      solver.Add(solver.Sum([sections[(j, i)] != k for k in certified_sections]) == 0) """
  #6. Sections are staffed at least by n employees based on the input df.
  # employee i works at hour j in section[i][j]. at hour j, for each section id k, sum(section values that are k) >= min_val should be true
  sections_cols = sections_df.columns[-1*(section_count - 1):]
  temp_arr = sections_df[sections_cols].as_matrix()#.toarray() #j,k array sections = i, j
  print(temp_arr.shape)
  for j in range(hours_count):
    for k in range(temp_arr.shape[1]):
      min_val = temp_arr[j][k]
      solver.Add(solver.Sum([sections[(i,j)] == k+1 for i in range(employee_count)   ]) >= int(min_val))
  #7. Break can be only after 3rd hour and before 3rd hour at end.
  #8. Run optimizer
  print(sections_df)
  print(employees_df)
  print(sections_flat)
  db = solver.Phase(sections_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
  _ = """solution = solver.Assignment()
  solution.Add(sections_flat)
  collector = solver.AllSolutionCollector(solution)
  solver.Solve(db, [collector])
  print("Solutions found:", collector.SolutionCount())
  print("Time:", solver.WallTime(), "ms")
  print()"""
  solver.NewSearch(db)
  num_solutions = 0
  print(num_solutions)
  while solver.NextSolution():
    num_solutions += 1
    print(num_solutions)
    pass
  solver.EndSearch()

  return

sdf, edf = get_df()
edf['Preferred Start of shift'] = 9.0
edf['Preferred end of shift'] = 17.0
edf['earliest available start'] = 8.0
edf['latest available end '] = 18.0

get_optimized_answer(sdf[["Time", "Section 1", "Section 2"]], edf)
