import pandas as pd, numpy as np, time, heapq
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

def get_subs_employee(thisemp, section, hour, enw, edf):  #enw = E x H
  eslice =np.array(enw)[:, hour] # E X 1
  for i in range(eslice.shape[0]):
    print(i)
    if i != thisemp and eslice[i] and str(section) in edf.loc[i].sectioncertifications:
      return i
  return -1
  
def fill_breaks(ehm, surplus, enw, free_employees, edf, ecols): #ehm: E x H, surplus H x 5, enw: E x H, free employees 1d index of last resort employees
  secol, eecol = ecols
  brehm = np.transpose(ehm)
  print(brehm.shape, surplus.shape, free_employees)

  for i in range(brehm.shape[0]):
    if i in free_employees[0]:
      continue
    bs, be = (edf.loc[i][secol] * HOUR_UNIT) + BREAK_UNIT , (edf.loc[i][eecol] * HOUR_UNIT) - BREAK_UNIT
    btimes = brehm[i][bs: be] # Each hour section.
    print("Total valid break units", btimes.shape)
    tarr = np.array([surplus[j + bs][btimes[j] - 1] for j in range(btimes.shape[0])    ])
    t1, t2  = heapq.nlargest(MAX_BREAKS, range(len(tarr)), tarr.take)
    max1, max2 = tarr[t1], tarr[t2]

    free_pool = max1 <= 0
    if not free_pool:
      sedit1 = brehm[i][bs + t1]
      e1_idx = get_subs_employee(i, sedit1, bs + t1, enw, edf) # Get from enw, an emp who is not working in this section at this hour, but is qualified to
      if e1_idx < 0:
        free_pool = True
      else:
        brehm[i][bs + t1] = -1     
        brehm[e1_idx][bs + t1] = sedit1
        enw[e1_idx][bs + t1] = True
        surplus[bs + t1][sedit1 - 1] -= 1
      if free_pool:
        pass #TODO: Pull from free employees

    free_pool = max2<= 0 # TODO: 1 Loop for those 2
    if not free_pool:
      sedit2 = brehm[i][bs + t2]
      e2_idx = get_subs_employee(i, sedit2, bs + t2, enw, edf) # Get from enw, an emp who is not working in this section at this hour, but is qualified to
      if e2_idx < 0:
        free_pool = True
      else:
        brehm[i][bs + t2] = -1
        brehm[e2_idx][bs + t2] = sedit2
        enw[e2_idx][bs + t2] = True
        surplus[bs + t2][sedit2 - 1] -= 1
      if free_pool:
        pass #TODO: Pull from free employees

    print("Max Idx in subsection", t1, t2)
  return brehm.transpose(), True

def fill_free_hours(op, edf, tot_hours, ecols):
  secol, eecol = ecols
  filled = np.transpose(op)
  free_employees = np.where(np.all(filled == 0, axis = 1))
  print(free_employees)
  enw = [[ False for h in range(tot_hours) ] for i in range(edf.shape[0])]
  for i in range(filled.shape[0]):
    idx = np.where(filled[i] > 0)[0][0] if np.where(filled[i] > 0)[0].size > 0 else 1
    for j in range(edf.loc[i][secol], idx):
      enw[i][j] = True
      filled[i][j] = filled[i][idx]
    for j in range(idx, edf.loc[i][eecol]*2):
      if filled[i][j] == 0 and filled[i][j-1]>0:
        enw[i][j] = True
        filled[i][j] = filled[i][j-1]   
  return filled.transpose(), enw, free_employees
   
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

  bsolfound = False
  if solfound:
    op, enw, free_employees = fill_free_hours(op, edf, sdf.shape[0], ecols)
    print(op.shape)
    ecount = np.array([[0 for i in range(len(scolumns) + 1) ] for h in range(len(sdf))])      
    for i in range(op.shape[0]):
      u, c = np.unique(op[i], return_counts = True)
      d = dict(zip(u, c))
      for k, v in d.items():
        if k != 0:
          ecount[i][k] = v
    surplus = np.array([ecount[i][1:] - sdf[scolumns].loc[i].as_matrix() for i in range(ecount.shape[0])] )
    op, bsolfound = fill_breaks(op, surplus, enw, free_employees, edf, ecols)
  return op, pi_idx, solfound, bsolfound

def main(sf, ef):
  sdf, edf = get_df(sf, ef)
  op1, invalid_hours, solfound, bsolfound = ans_row(sdf, edf, ["preferredstart", "preferredend"], None, None)
  print(invalid_hours)
  pd.DataFrame(op1).transpose().to_csv("./prefop.csv")
  if not solfound:
    print("############################################################################################################################################")
    op2, invalid_hours, solfound, bsolfound = ans_row(sdf, edf, ["earlieststart", "latestend"], invalid_hours, op1)
    print(op2.shape, invalid_hours)  
    pd.DataFrame(op2).transpose().to_csv("./strictop1.csv")

if __name__ == "__main__":
  start = time.time()
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("section")
  parser.add_argument("employee")
  args = parser.parse_args()
  print(args.section, args.employee)
  main(args.section, args.employee)
  print("Total time = ", time.time() - start)
