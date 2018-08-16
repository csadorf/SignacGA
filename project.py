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

@Project.label
def isSorted(job):
    """
    returns True if 'rank' is present in the
    job document
    """
    return 'rank' in job.document

@Project.label
def hasCost(job):
    """
    returns True is 'cost' is present in the
    job document
    """
    return 'cost' in job.document

@Project.label
def isOptimized(job):
    """
    returns True if the optimized flag is in the
    project document. This is used to effectively finish
    """
    return 'optimized' in job._project.document

@Project.label
def inGen(job):
    gNum = job._project.document.generation.n
    if 'generation' in job.document:
        return job.document.generation == gNum
    else:
        return False

@Project.label
def toSort(job):
    project = job._project
    gNum = project.document.generation.n
    return all(('cost' in job.document and 'rank' not in job.document) for job in project.find_jobs(doc_filter={'generation': gNum}))

@Project.operation
@Project.pre(inGen)
@Project.pre(lambda job: 'optimized' not in job._project.document)
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

@Project.operation
@Project.pre(lambda job: 'optimized' not in job._project.document)
@Project.pre(inGen)
@Project.pre(toSort)
@Project.post(lambda job: 'rank' in job.document)
def sortGeneration(job):
    genNum = job._project.document.generation.n
    if "gDict" in job._project.document.generation:
        sortDict = job._project.document.generation.gDict
    else:
        # first, get all the jobs in the generation
        lGeneration = Project().find_jobs(doc_filter={'generation': genNum})
        costList = [(j.get_id(), j.document.cost) for j in lGeneration]
        sortList = np.array(costList, dtype=[('id', '|S32'), ('cost', int)])
        sortList.sort(order='cost')
        gDict = dict()
        for i, (lID, lCost) in enumerate(sortList):
            lDict = dict()
            lDict["cost"] = int(lCost)
            lDict["rank"] = i
            gDict[lID.decode('UTF-8')] = lDict
        job._project.document.generation.gDict = gDict
        np.save("Generation.{}.npy".format(genNum), sortList)
        sortDict = gDict
    rank = sortDict[job.get_id()]['rank']
    job.document.rank = rank

@Project.operation
@Project.pre(lambda job: 'optimized' not in job._project.document)
@Project.pre(lambda job: 'rank' in job.document)
@Project.pre(inGen)
@Project.post(lambda job: 'rank' not in job.document)
def nextGeneration(job):
    gNum = job._project.document.generation.n

    # job.document.generation = gNum + 1
    # job.document.pop('rank')

    job.document.generation = gNum + 1
    job.document.pop('rank')
    project = job._project
    newCode = util._mutate(job.sp.code, 0.5)
    statepoint = dict(length=len(job.sp.goal),
                       goal=job.sp.goal,
                       code=newCode,
                       seed=job.sp.seed)
    project.open_job(statepoint).init()
    lJob = project.open_job(statepoint)
    lJob.document.generation = gNum+1

    lGeneration = project.find_jobs(doc_filter={'generation': gNum, 'rank': {'$exists': True}})
    if len(lGeneration) == 0:
        job._project.document.generation.pop('gDict')
        job._project.document.generation.n = gNum + 1

# @Project.operation
# @Project.pre(lambda job: 'optimized' not in job._project.document)
# @Project.pre(lambda job: 'rank' in job.document)
# @Project.pre(inGen)
# @Project.post(lambda job: 'rank' not in job.document)
# def nextGeneration(job):
#     # only the first will perform the mating
#     # lGeneration = Project().find_jobs(doc_filter={'generation': Project().document.generation})
#     gNum = job._project.document.generation.n
#     # load the generation file
#     genFile = np.load("Generation.{}.npy".format(int(Project().document.generation.n)))
#     sortDict = job._project.document.generation.gDict
#     n = len(sortDict)
#     # create new children
#     # they do not have ranks
#     if job.document.rank == 0:
#         # create children
#         codeA = job.sp.code
#         # get the other candidate
#         j = Project().open_job(id=genFile['id'][1].decode('UTF-8'))
#         codeB = j.sp.code
#         # get new code
#         newA, newB = util._mate(codeA, codeB)
#         # create new jobs
#         statepointA = dict(length=len(job.sp.goal),
#                            goal=job.sp.goal,
#                            code=newA,
#                            seed=job.sp.seed)
#         Project().open_job(statepointA).init()
#         lJob = Project().open_job(statepointA)
#         lJob.document.generation = job.document.generation+1
#         statepointB = dict(length=len(job.sp.goal),
#                            goal=job.sp.goal,
#                            code=newB,
#                            seed=job.sp.seed)
#         Project().open_job(statepointB).init()
#         lJob = Project().open_job(statepointB)
#         lJob.document.generation = job.document.generation+1
#     # keep parents as-is
#     if job.document.rank < 2:
#         statepoint = dict(length=len(job.sp.goal),
#                            goal=job.sp.goal,
#                            code=job.sp.code,
#                            seed=job.sp.seed)
#         Project().open_job(statepoint).init()
#         lJob = Project().open_job(statepoint)
#         lJob.document.generation = job.document.generation+1
#         lJob.document.pop('rank')
#     elif job.document.rank > (n - 4):
#         job.document.pop('rank')
#     else:
#         newCode = util._mutate(job.sp.code, 0.5)
#         statepoint = dict(length=len(job.sp.goal),
#                            goal=job.sp.goal,
#                            code=newCode,
#                            seed=job.sp.seed)
#         Project().open_job(statepoint).init()
#         lJob = Project().open_job(statepoint)
#         lJob.document.generation = job.document.generation+1
#         if 'rank' in lJob.document:
#             lJob.document.pop('rank')
#         if 'rank' in job.document:
#             job.document.pop('rank')
#     # finally, check to get rid of and increment generation
#     # check if no more ranks exist
#     lGeneration = Project().find_jobs(doc_filter={'generation': gNum, 'rank': {'$exists': True}})
#     if len(lGeneration) == 0:
#         job._project.document.generation.pop('gDict')
#         job._project.document.generation.n = gNum + 1

if __name__ == "__main__":
    Project().main()
