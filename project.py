"""
This module contains operation functions for this project.

The workflow defined in this file can be executed from the
command line with

    $ python project.py run [job_id [job_id ...]]

See also: $ python src/project.py --help
"""

from flow import FlowProject
import util
import numpy as np
import os.path

class Project(FlowProject):
    pass

# @Project.label
# def retFalse(job):
#     return False

# @Project.label
# def isEligible(job):
#     if 'eligible' in job.document:
#         if job.document.eligible == True:
#             return True
#         else:
#             return False
#     else:
#         return False

# @Project.label
# def isNotEligible(job):
#     if 'eligible' in job.document:
#         if job.document.eligible == True:
#             return False
#         else:
#             return True
#     else:
#         return False

@Project.label
def isSorted(job):
    return 'rank' in job.document

@Project.label
def hasCost(job):
    return 'cost' in job.document

# @Project.label
# def statusCost(job):
#     return Project().document.status.cost

# @Project.label
# def statusSort(job):
#     return Project().document.status.sort

# @Project.label
# def statusGenerate(job):
#     return Project().document.status.generate

@Project.operation
@Project.pre(lambda job: 'cost' not in job.document)
@Project.post(lambda job: 'cost' in job.document)
def calcCost(job):
    """
    Calculate the cost of a given code by its
    distance from the goal using ASCII key codes
    """
    costCode = np.array([ord(i) for i in job.sp.code])
    costGoal = np.array([ord(i) for i in job.sp.goal])
    cost = int(np.power(np.sum(costCode - costGoal), 2))
    job.document.cost = cost
    if job.document.cost == 0:
        job._project.document.optimized = True
    # project = job._project
    # genNum = project.document.generation
    # project.document.status.cost = not all(job.doc.get('cost', False) for job in project.find_jobs(doc_filter={'generation': genNum}))
    # project.document.status.sort = all(job.doc.get('cost', False) for job in project.find_jobs(doc_filter={'generation': genNum}))

@Project.operation
@Project.pre(lambda job: 'cost' in job.document)
@Project.post(lambda job: 'rank' in job.document)
def sortGeneration(job):
    genNum = job._project.document.generation
    if os.path.isfile("Generation.{}.npy".format(int(genNum))):
        sortList = np.load("Generation.{}.npy".format(int(genNum)))
    else:
        # first, get all the jobs in the generation
        lGeneration = Project().find_jobs(doc_filter={'generation': genNum})
        costList = [(j.get_id(), j.document.cost) for j in lGeneration]
        sortList = np.array(costList, dtype=[('id', '|S32'), ('cost', int)])
        sortList.sort(order='cost')
        np.save("Generation.{}.npy".format(genNum), sortList)
    rank = int(np.where(sortList['cost'] == job.document.cost)[0][0])
    job.document.rank = rank
    # project = job._project
    # project.document.status.sort = not all('rank' in job.document for job in project.find_jobs(doc_filter={'generation': genNum}))
    # project.document.status.generate = all('rank' in job.document for job in project.find_jobs(doc_filter={'generation': genNum}))

@Project.operation
# @Project.pre.after(retFalse)
# @Project.pre.after(hasCost)
# @Project.pre.after(isSorted)
# @Project.pre.after(statusGenerate)
# @Project.pre.after(isEligible)
# @Project.post(isNotEligible)
@Project.pre(lambda job: 'rank' in job.document)
# not sure what the post condition should be
# @Project.post(statusCost)
# Except...that's not right...
# @Project.post(lambda job: 'optimized' in job._project.document)
def nextGeneration(job):
    # only the first will perform the mating
    # lGeneration = Project().find_jobs(doc_filter={'generation': Project().document.generation})
    # load the generation file
    genFile = np.load("Generation.{}.npy".format(int(Project().document.generation)))
    n = len(genFile)
    if job.document.rank == 0:
        # create children
        codeA = job.sp.code
        # get the other candidate
        j = Project().open_job(id=genFile['id'][1].decode('UTF-8'))
        codeB = j.sp.code
        # get new code
        newA, newB = util._mate(codeA, codeB)
        # create new jobs
        statepointA = dict(length=len(job.sp.goal),
                           goal=job.sp.goal,
                           code=newA,
                           seed=job.sp.seed)
        Project().open_job(statepointA).init()
        lJob = Project().open_job(statepointA)
        lJob.document.generation = job.document.generation+1
        statepointB = dict(length=len(job.sp.goal),
                           goal=job.sp.goal,
                           code=newB,
                           seed=job.sp.seed)
        Project().open_job(statepointB).init()
        lJob = Project().open_job(statepointB)
        lJob.document.generation = job.document.generation+1
    if job.document.rank < 2:
        statepoint = dict(length=len(job.sp.goal),
                           goal=job.sp.goal,
                           code=job.sp.code,
                           seed=job.sp.seed)
        Project().open_job(statepoint).init()
        lJob = Project().open_job(statepoint)
        lJob.document.generation = job.document.generation+1
        lJob.document.pop('rank')
    elif job.document.rank > (n - 4):
        pass
    else:
        newCode = util._mutate(job.sp.code, 0.5)
        statepoint = dict(length=len(job.sp.goal),
                           goal=job.sp.goal,
                           code=newCode,
                           seed=job.sp.seed)
        Project().open_job(statepoint).init()
        lJob = Project().open_job(statepoint)
        lJob.document.generation = job.document.generation+1
        if 'rank' in lJob.document:
            lJob.document.pop('rank')


if __name__ == "__main__":
    Project().main()
