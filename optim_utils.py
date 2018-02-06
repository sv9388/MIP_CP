import pandas as pd
from ortools.constraint_solver import pywrapcp

MAX_BREAKS = 2 #TODO: 2
BREAK_UNIT = 6 #TODO: Six units in actual file

def get_df(sf, ef):
  section_df = pd.read_csv(sf) #'./sections.csv') #TODO: Dynamic filenames as ip
  employees_df = pd.read_csv(ef)# './employees.csv')
  return section_df, employees_df

# meet all requirements per section at minimum labour-hours
def get_optimized_answer(sections_df, employees_df):
  #0. Variables
  section_count = sections_df.shape[1]-1 
  employee_count = employees_df.shape[0]
  hours_count = sections_df.shape[0]
  solver = pywrapcp.Solver("schedule_sections")
  #1. Assign sections to employees.
  sections = {}
  for j in range(employee_count):
    for i in range(hours_count):
      sections[(j, i)] = solver.IntVar(0, section_count - 1, "sections(%i,%i)" % (j, i))
  print("Section Variables Count = ", len(sections))
  sections_flat = [sections[(j, i)] for j in range(employee_count) for i in range(hours_count)]
  #2. Assigned to section zero means not working
  #3. 1 employee 1 section at a time.
  employees = {}
  for i in range(section_count):
    sec_emp_count = sections_df.loc[i][sections_df.columns[1 + i]]
    sec_emp_count = int(sec_emp_count)
    for j in range(hours_count):
      for k in range(sec_emp_count):
        employees[(i, j, k)] = solver.IntVar(0, employee_count - 1, "employees(%i,%i, %i)" %(i, j, k))
  #relationship between sections and employees. One employee in one section tops. one section should contain this employee
  for i in range(hours_count):
    sections_for_houri = [sections[(j, i)] for j in range(employee_count)] #In a given hour i, each o employees j are at section[j,i]
    for j in range(section_count):
      sec_emp_count = int(sections_df.loc[j][sections_df.columns[1 + j]])
      solver.Add(solver.Sum([employees[(j, i, k)].IndexOf(sections_for_houri)==j for k in range(sec_emp_count)])==sec_emp_count)
  #4. Employees work 6 to 8 hours. Doesn't work before start time and doesn't work after end time.
  for j in range(employee_count):
    pref_start = employees_df.loc[j]['preferredstart']
    print(pref_start)
    pref_start_idx = sections_df[sections_df['time'] == pref_start].index[0]
    pref_end = employees_df.loc[j]['preferredend']
    pref_end_idx = sections_df[sections_df['time'] == pref_end].index[0]
    print(pref_start, pref_start_idx)
    print(pref_end, pref_end_idx)
    for i in range(pref_start_idx):
      solver.Add(sections[(j, i)] == 0)
    for i in range(pref_end_idx + 1, hours_count):
      solver.Add(sections[(j, i)] == 0)
  #5. Employees work only in certified sections
  for j in range(employee_count):
    certified_sections = employees_df.loc[j]['sectioncertifications'].split(",")
    certified_sections = [0] + [int(x) for x in certified_sections]
    print(certified_sections)
    for i in range(hours_count):
      solver.Add(solver.IsMemberVar(sections[(j,i)], certified_sections) > 0)
  #6. Sections are staffed at least by n employees based on the input df.
  # employee i works at hour j in section[i][j]. at hour j, for each section id k, sum(section values that are k) >= min_val should be true
  sections_cols = sections_df.columns[-1*(section_count - 1):]
  temp_arr = sections_df[sections_cols].as_matrix()#.toarray() #j,k array sections = i, j
  print(temp_arr)
  for j in range(hours_count):
    for k in range(temp_arr.shape[1]):
      min_val = temp_arr[j][k]
      solver.Add(solver.Sum([ sections[(i,j)] == k+1 for i in range(employee_count)]) >= int(min_val))
  #7a. Break can be only after 3rd hour and before 3rd hour at end. every employee 
  #7b. Break can be utmost 1 hour
  for i in range(employee_count):
    pref_start = employees_df.loc[i]['preferredstart']
    print(pref_start)
    pref_start_idx = sections_df[sections_df['time'] == pref_start].index[0]
    pref_end = employees_df.loc[i]['preferredend']
    pref_end_idx = sections_df[sections_df['time'] == pref_end].index[0]
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_start_idx, pref_start_idx + BREAK_UNIT)]) == 0)
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_end_idx - BREAK_UNIT, pref_end_idx)]) == 0)
    solver.Add(solver.Sum([sections[(i, j)] == 0 for j in range(pref_start_idx, pref_end_idx)]) <= MAX_BREAKS)
  #8. Run optimizer
  print("Phasing", solver)
  db = solver.Phase(sections_flat, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE)
  solution = solver.Assignment()
  solution.Add(sections_flat)
  collector = solver.FirstSolutionCollector(solution)
  print("Solving", solver, solution)
  solver.Solve(db, [collector])
  print("Solutions found:", collector.SolutionCount())
  print("Time:", solver.WallTime(), "ms")
  print()
  print(sections_df)
  print(employees_df)
  for sol in range(collector.SolutionCount()):
    print("Solution number" , sol, '\n')
    op = [[collector.Value(sol, sections[(i, j)]) for j in range(hours_count)] for i in range(employee_count)]
    opcolumns =  [sections_df.loc[i].time for i in range(hours_count)]
    opindex   =  [employees_df.loc[i].employeeid for i in range(employee_count)]
    opdf = pd.DataFrame(op, index = opindex, columns=opcolumns)
    print(opdf) #"Employee", j, "assigned to task",  collector.Value(sol, sections[(j, i)]))

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  sdf['section0'] = 0
  edf['preferredstart'] = 9.0
  print(sdf['time'])
  edf['preferredend'] = 12.0
  edf['earlieststart'] = 8.0
  edf['latestend'] = 18.0
  #sedf = sdf.iloc[15:25][["time", "section0", "section1", "section2"]]
  #print(sedf)
  #sedf = sedf.reset_index()
  #sedf = sedf.drop(columns = ['index'])
  print(sdf.columns, edf.columns)
  get_optimized_answer(sdf, edf)

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args)
  main()
