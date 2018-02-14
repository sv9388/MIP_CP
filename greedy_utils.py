import pandas as pd, numpy as np, time
from ortools.constraint_solver import pywrapcp

MAX_BREAKS = 2
BREAK_UNIT = 4
HOUR_UNIT = 2 # How many hour slices make an hour?

def get_df(sf, ef):
  section_df = pd.read_csv(sf)
  employees_df = pd.read_csv(ef)
  return section_df, employees_df

scolumns = ['section1', 'section2', 'section3', 'section4', 'section5']
 
def get_optimized_answer(arr, emp_indices, ecerts):
  # arr = 1D arr of min section requirement per hour
  # emp_indices = employee df with times as indices in arr
  op = [0 for i in range(len(emp_indices))]
  solfound = (sum(arr) == 0)
  if len(emp_indices) == 0 or sum(arr) == 0:
    return op, solfound
  solver = pywrapcp.Solver("schedule_sections")
  employee_count = len(emp_indices)
  section_count = len(arr) + 1 
  sections = [solver.IntVar(0, section_count-1, "sections(%i)" % i) for i in range(employee_count)]
  # 1. An employee must be in certified section only
  for i in range(employee_count):
    empcerts = ecerts[i].split(",")
    empcerts = list([0] + [int(x) for x in empcerts])
    solver.Add(solver.Sum([solver.IsMemberVar(sections[i], empcerts)]) == 1)
  # 2. Total section requirement should be met.  
  for i in range(1, section_count):
    solver.Add(solver.Sum([sections[j] == i for j in range(employee_count) ]) == int(arr[i-1]))
  # Optimiser
  db = solver.Phase(sections, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_RANDOM_VALUE  )  
  solver.NewSearch(db) #, [solver.SearchTrace("")])
  if solver.NextSolution():
    solfound = True
    op = [sections[i].Value() for i in range(employee_count)]
  solver.EndSearch()
  return op, solfound

def ans_row(sdf, edf, ecols, invalid_hours = None, existing_op = None):
  secol, eecol = ecols
  op =  existing_op if existing_op else [[0 for  i in range(edf.shape[0])] for  j in range(sdf.shape[0])]
  indices = invalid_hours if invalid_hours else range(sdf.shape[0])
  pi_idx = []
  row_section = lambda i : [int(x) for x in sdf.loc[i][scolumns].as_matrix().tolist()]
  solfound = True
  for i in indices: 
    r = row_section(i)
    emps = edf[(edf[secol]<= sdf.loc[i].time) & (sdf.loc[i].time <= edf[eecol])]
    eidx = list(emps.index)
    asgn = [0 for j in range(edf.shape[0])]
    certs = emps.sectioncertifications.as_matrix()
    svals, t = get_optimized_answer(r, eidx, certs)
    if not t:
      pi_idx.append(i)
    solfound = solfound & t
    for j in range(len(eidx)):
      idx = eidx[j]
      asgn[idx] = svals[j]
    op[i] = asgn
  df = pd.DataFrame(op)
  print(df.shape)
  print(solfound)

  if solfound:
    # Fill non working assignments with filled except 2 zeroes
    op = np.array(op).transpose().tolist()
    for i in range(len(op)):
      print("Existing row: ", op[i])
      for j in range(1, edf.loc[i][eecol]*2):
        if op[i][j] == 0 and op[i][j-1]>0:
          op[i][j] = op[i][j-1]
      print("Modified row: ", op[i])    
  _ = """if solfound:
    op, solfound = process_breaks(op, sdf[scolumns].as_matrix(), edf[secol] * HOUR_UNIT + BREAK_UNIT, edf[eecol] * HOUR_UNIT - BREAK_UNIT, edf.sectioncertifications)"""
  return op, pi_idx, solfound

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  op1, invalid_hours, solfound = ans_row(sdf, edf, ["preferredstart", "preferredend"], None, None)
  print(invalid_hours)
  pd.DataFrame(op1).to_csv("./prefop.csv")
  if not solfound:
    print("############################################################################################################################################")
    op2, invalid_hours, solfound = ans_row(sdf, edf, ["earlieststart", "latestend"], invalid_hours, op1)
    print(invalid_hours)  
    pd.DataFrame(op2).to_csv("./strictop1.csv")

if __name__ == "__main__":
  start = time.time()
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
  print("TOtal time = ", time.time() - start)
