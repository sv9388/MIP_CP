import pandas as pd, numpy as np
from ortools.constraint_solver import pywrapcp

MAX_BREAKS = 2 #TODO: 2
BREAK_UNIT = 6 #TODO: Six units in actual file

def get_df(sf, ef):
  section_df = pd.read_csv(sf, index_col = 0) #TODO: Dynamic filenames as ip
  employees_df = pd.read_csv(ef)
  return section_df, employees_df

# meet all requirements per section at minimum labour-hours
def get_optimized_answer(sections_df, employees_df, cols):
  start_col = cols[0]
  end_col = cols[1]
  #0. Variables
  section_count = sections_df.shape[1]-1
  employee_count = employees_df.shape[0]
  hours_count = sections_df.shape[0]
  solver = pywrapcp.Solver("schedule_sections")
  #1. Assign sections to /employees.
  sections = {}
  for j in range(employee_count):
    for i in range(hours_count):
      sections[(j, i)] = solver.IntVar(0, section_count-1, "sections(%i,%i)" % (j, i))
  sections_flat = [sections[(j, i)] for j in range(employee_count) for i in range(hours_count)]
  #2. Assigned to section zero means not working
  #3. 1 employee 1 section at a time.
  #4. Employees work 6 to 8 hours. Doesn't work before start time and doesn't work after end time.
  for j in range(employee_count):
    pref_start = employees_df.loc[j][start_col]
    pref_start_idx = sections_df[sections_df['time'] == pref_start].index[0]
    pref_end = employees_df.loc[j][end_col]
    pref_end_idx = sections_df[sections_df['time'] == pref_end].index[0] 
    for i in range(pref_start_idx):
      solver.Add(sections[(j, i)] == 0)
    for i in range(pref_end_idx + 1, hours_count):
      solver.Add(sections[(j, i)] == 0)
  #5. Employees work only in certified sections
  for j in range(employee_count):
    pref_start = employees_df.loc[j][start_col]
    pref_start_idx = sections_df[sections_df['time'] == pref_start].index[0]
    pref_end = employees_df.loc[j][end_col]
    pref_end_idx = sections_df[sections_df['time'] == pref_end].index[0]
    certified_sections = employees_df.loc[j]['sectioncertifications'].split(",")
    certified_sections = [0] + [int(x) for x in certified_sections]
    incerts = [solver.IsMemberVar(sections[(j, i)], certified_sections) for i in range(pref_start_idx, pref_end_idx)]
    solver.Add(solver.Sum(incerts) <= int(pref_end_idx - pref_start_idx + 1))
  #6. Sections are staffed at least by n employees based on the input df.
  # employee i works at hour j in section[i][j]. at hour j, for each section id k, sum(section values that are k) >= min_val should be true
  sections_cols = sections_df.columns[1:]
  temp_arr = sections_df[sections_cols].as_matrix()#.toarray() #j,k array sections = i, j
  print(temp_arr.shape)
  for j in range(hours_count):
    for k in range(temp_arr.shape[1]):
      min_val = temp_arr[j][k]
      solver.Add(solver.Sum([sections[(i,j)] == k for i in range(employee_count)]) >= int(min_val))
  #7a. Break can be only after 3rd hour and before 3rd hour at end. every employee
  #7b. Break can be utmost 1 hour
  for i in range(employee_count):
    pref_start = employees_df.loc[i][start_col]   
    pref_start_idx = sections_df[sections_df['time'] == pref_start].index[0]
    pref_end = employees_df.loc[i][end_col]
    pref_end_idx = sections_df[sections_df['time'] == pref_end].index[0]
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_start_idx, pref_start_idx + BREAK_UNIT)]) == 0)
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_end_idx - BREAK_UNIT, pref_end_idx)]) == 0)
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_start_idx, pref_end_idx)]) == MAX_BREAKS)
  #8. Run optimizer
  db = solver.Phase(sections_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_RANDOM_VALUE)
  solver.NewSearch(db, [solver.SearchTrace("")])
  op =[]
  if solver.NextSolution():
    op = [[sections[(i, j)].Value() for j in range(hours_count)] for i in range(employee_count)]
  solver.EndSearch()

  print("Time:", solver.WallTime(), "ms")
  print()
  opdf = pd.DataFrame()
  opcolumns =  [sections_df.loc[i].time for i in range(hours_count)]
  opindex   =  [employees_df.loc[i].employeeid for i in range(employee_count)]
  opdf = pd.DataFrame(op, index = opindex, columns=opcolumns) 

  return opdf #df #"Employee", j, "assigned to task",  collector.Value(sol, sections[(j, i)]))

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  sdf['section0'] = 0
  scols = ['time', 'section0', 'section1', 'section2', 'section3', 'section4', 'section5' ]
  df = get_optimized_answer(sdf[scols], edf, ["preferredstart", "preferredend"])
  if df.dropna().empty:
    df = get_optimized_answer(sdf[scols], edf, ["earlieststart", "latestend"])
  if df.dropna().empty:
    print("Not all hours had valid criteria met.")
  print(df)

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
