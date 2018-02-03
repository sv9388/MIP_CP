Command Line Setup:
===================
1. Clone this repo using ```git clone https://github.com/sv9388/MIP_CP.git``` in Unix or using the repo name as the input for Github client in windows.
2. Install python3 and python3-pip
3. Go to the root folder of the project.
4. Install the app requirements using the command ```pip install -r requirements.txt```
5. In the same root folder, upload two csvs. 
   * "sections.csv": Has the section requirements. Columns should be [time, section1, section2, ... sectionn] where n is the total number of sections
   * "employees.csv": Has the employee details. Columns should be [employeeid, employeename, sectioncertifications, preferredstart, preferredend, earlieststart, latestend] without any trailing spaces.
6. Run the command ```python3 optim_utils.py```
7. The output will show the time taken to determine the solutions and the actual solutions as a matrix of employee id vs hours assigned. The values of the matrix at a given cell (i, j) will be the section to which employee i is assigned to at hour j
