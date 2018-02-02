from __future__ import print_function
import sys
from ortools.constraint_solver import pywrapcp

def main():
  # Creates the solver.
  solver = pywrapcp.Solver("schedule_sections")

  num_employees = 3
  num_sections = 5
  num_hours = 50 # 49 + 1 (for not working)
  # [START]
  # Create section variables.
  sections = {}

  _ = """for j in range(num_employees):
    for i in range(num_hours):
      sections[(j, i)] = solver.IntVar(0, num_sections - 1, "sections(%i,%i)" % (j, i))
  sections_flat = [sections[(j, i)] for j in range(num_employees) for i in range(num_hours)]"""

  # Create employee variables.
  employees = {}

  for j in range(num_sections):
    for i in range(num_hours):
      employees[(j, i)] = solver.IntVar(0, num_employees - 1, "section%d hour%d" % (j,i))

  # Set relationships between sections and employees.
  for hour in range(num_hours):
    employees_for_hour = [employees[(j, hour)] for j in range(num_sections)]

    for j in range(num_employees):
      s = sections[(j, hour)]
      solver.Add(s.IndexOf(employees_for_hour) == j)

  # Make assignments different on each hour
  for i in range(num_hours):
    solver.Add(solver.AllDifferent([sections[(j, i)] for j in range(num_employees)]))
    solver.Add(solver.AllDifferent([employees[(j, i)] for j in range(num_sections)]))
  # Each employee works 5 or 6 hours in a week.
  for j in range(num_employees):
    solver.Add(solver.Sum([sections[(j, i)] > 0 for i in range(num_hours)]) >= 5)
    solver.Add(solver.Sum([sections[(j, i)] > 0 for i in range(num_hours)]) <= 6)
  # Create works_section variables. works_section[(i, j)] is True if employee
  # i works section j at least once during the week.
  works_section = {}

  for i in range(num_employees):
    for j in range(num_sections):
      works_section[(i, j)] = solver.BoolVar('section%d employee%d' % (i, j))

  for i in range(num_employees):
    for j in range(num_sections):
      solver.Add(works_section[(i, j)] == solver.Max([sections[(i, k)] == j for k in range(num_hours)]))

  # For each section (other than 0), at most 2 employees are assigned to that section
  # during the week.
  for j in range(1, num_sections):
    solver.Add(solver.Sum([works_section[(i, j)] for i in range(num_employees)]) <= 2)
  # If s employees works sections 2 or 3 on, he must also work that section the previous
  # hour or the following hour.
  solver.Add(solver.Max(employees[(2, 0)] == employees[(2, 1)], employees[(2, 1)] == employees[(2, 2)]) == 1)
  solver.Add(solver.Max(employees[(2, 1)] == employees[(2, 2)], employees[(2, 2)] == employees[(2, 3)]) == 1)
  solver.Add(solver.Max(employees[(2, 2)] == employees[(2, 3)], employees[(2, 3)] == employees[(2, 4)]) == 1)
  solver.Add(solver.Max(employees[(2, 3)] == employees[(2, 4)], employees[(2, 4)] == employees[(2, 5)]) == 1)
  solver.Add(solver.Max(employees[(2, 4)] == employees[(2, 5)], employees[(2, 5)] == employees[(2, 6)]) == 1)
  solver.Add(solver.Max(employees[(2, 5)] == employees[(2, 6)], employees[(2, 6)] == employees[(2, 0)]) == 1)
  solver.Add(solver.Max(employees[(2, 6)] == employees[(2, 0)], employees[(2, 0)] == employees[(2, 1)]) == 1)

  solver.Add(solver.Max(employees[(3, 0)] == employees[(3, 1)], employees[(3, 1)] == employees[(3, 2)]) == 1)
  solver.Add(solver.Max(employees[(3, 1)] == employees[(3, 2)], employees[(3, 2)] == employees[(3, 3)]) == 1)
  solver.Add(solver.Max(employees[(3, 2)] == employees[(3, 3)], employees[(3, 3)] == employees[(3, 4)]) == 1)
  solver.Add(solver.Max(employees[(3, 3)] == employees[(3, 4)], employees[(3, 4)] == employees[(3, 5)]) == 1)
  solver.Add(solver.Max(employees[(3, 4)] == employees[(3, 5)], employees[(3, 5)] == employees[(3, 6)]) == 1)
  solver.Add(solver.Max(employees[(3, 5)] == employees[(3, 6)], employees[(3, 6)] == employees[(3, 0)]) == 1)
  solver.Add(solver.Max(employees[(3, 6)] == employees[(3, 0)], employees[(3, 0)] == employees[(3, 1)]) == 1)
# Create the decision builder.
  db = solver.Phase(sections_flat, solver.CHOOSE_FIRST_UNBOUND,
                    solver.ASSIGN_MIN_VALUE)
# Create the solution collector.
  solution = solver.Assignment()
  solution.Add(sections_flat)
  collector = solver.AllSolutionCollector(solution)

  solver.Solve(db, [collector])
  print("Solutions found:", collector.SolutionCount())
  print("Time:", solver.WallTime(), "ms")
  print()
  # Display a few solutions picked at random.
  a_few_solutions = [859, 2034, 5091, 7003]

  for sol in a_few_solutions:
    print("Solution number" , sol, '\n')

    for i in range(num_hours):
      print("hour", i)
      for j in range(num_employees):
        print("employee", j, "assigned to task",
              collector.Value(sol, sections[(j, i)]))
      print()

if __name__ == "__main__":
  main()