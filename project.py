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
import time

MAX_NUM_GENERATIONS = 10000

def isMaster(job):
    """
    returns True is job is master; otherwise returns False
    """
    return job.sp.master

def getSimJobs(masterJob, simulated=None):
    """
    Get all the jobs that (don't) need simulated
    """
    # only look for non-master jobs
    filter = dict(master=False)
    if simulated is True or simulated is False:
        # return list of jobs where 'cost' exists
        # or does not exist
        doc_filter = {'cost': {'$exists': simulated}}
    elif simulated is None:
        doc_filter = None
    else:
        raise ValueError(simulated)
    return masterJob._project.find_jobs(filter, doc_filter)

class Project(FlowProject):
    pass

@Project.label
def simulated(job):
    """
    return True if a sub-job has a cost (has been simulated)
    return True if master job and all sub jobs are complete
    """
    if job.sp.master:
        return len(getSimJobs(job, simulated=False)) == 0
    else:
        return 'cost' in job.doc

@Project.label
def optimized(job):
    """
    returns True if the optimized flag is in the
    project document. This is used to effectively finish
    the optimization
    """
    if job._project.document.generation.n > MAX_NUM_GENERATIONS:
        return True
    else:
        return 'optimized' in job._project.document

@Project.label
def inGeneration(job):
    """
    Returns True if a job is in the current generation
    """
    if not job.sp.master:
        gNum = job._project.document.generation.n
        if 'generation' in job.document:
            return job.document.generation == gNum
        else:
            return False

@Project.operation
@Project.pre(lambda job: not optimized(job))
@Project.pre(lambda job: not isMaster(job))
@Project.pre(lambda job: 'cost' not in job.document)
@Project.post(simulated)
def calcCost(job):
    """
    Calculate the cost of a given code by its
    distance from the goal using ASCII key codes
    """
    costCode = np.array([ord(i) for i in job.sp.code])
    costGoal = np.array([ord(i) for i in job.sp.goal])
    # cost = int(np.power(np.sum(costCode - costGoal), 2))
    cost = int(np.sum(np.power(costCode - costGoal, 2)))
    job.document.cost = cost
    # time.sleep(0.5)
    if job.document.cost == 0:
        job._project.document.optimized = True
        f = open("optimized.txt", "w")
        f.write("optimized\n")
        f.close()

@Project.operation
@Project.pre(lambda job: not optimized(job))
@Project.pre(lambda job: isMaster(job))
@Project.pre(simulated)
@Project.post(optimized)
def nextGeneration(job):
    """
    iterate the optimization to the next generation:
    1. Sorts current generation by cost
    2. Crosses the best two
    3. Randomly mutates the rest
    4. Creates new random candidates to keep the generation size constant
    5. Removes "old" jobs because the time to search/index takes longer and longer
       and in this case, we don't really need to keep all of them around
    """
    startTime = time.time()
    project = job._project
    gNum = project.document.generation.n

    # find all jobs in this generation
    lGeneration = project.find_jobs(filter={'master': False}, doc_filter={'generation': gNum})
    # create a list and sort
    costList = [(j.get_id(), j.document.cost) for j in lGeneration]
    sortList = np.array(costList, dtype=[('id', '|S32'), ('cost', int)])
    sortList.sort(order='cost')
    print("generation: {}, cost: {}".format(gNum, sortList[0][1]))
    # now we go through and create the next generation
    for i, (lID, lCost) in enumerate(sortList):
        # get the job
        lJob = project.open_job(id=lID.decode('UTF-8'))
        # cross the best two
        if i == 0:
            codeA = lJob.sp.code
            jobB = project.open_job(id=sortList[1][0].decode('UTF-8'))
            codeB = jobB.sp.code
            newA, newB = util._mate(codeA, codeB)
            # create new jobs
            statepoint = dict(length=len(job.sp.goal),
                  goal=job.sp.goal,
                  code=newA,
                  seed=lJob.sp.seed,
                  master=False)
            project.open_job(statepoint).init()
            lA = project.open_job(statepoint)
            lA.document.generation = gNum + 1
            statepoint = dict(length=len(job.sp.goal),
                  goal=job.sp.goal,
                  code=newB,
                  seed=lJob.sp.seed,
                  master=False)
            project.open_job(statepoint).init()
            lB = project.open_job(statepoint)
            lB.document.generation = gNum + 1
        # mutate remaining sans last 4 (effectively drops the worst 4)
        if i < (len(sortList) - 4):
            newCode = util._mutate(lJob.sp.code, 0.5)
            statepoint = dict(length=len(job.sp.goal),
                              goal=job.sp.goal,
                              code=newCode,
                              seed=lJob.sp.seed,
                              master=False)
            project.open_job(statepoint).init()
            lJob = project.open_job(statepoint)
            lJob.document.generation = gNum + 1
    # find how many more statepoints are required to keep the generation size constant
    lGeneration = project.find_jobs(filter={'master': False}, doc_filter={'generation': gNum+1})
    nRemain = len(sortList) - len(lGeneration)
    while nRemain > 0:
        for i in range(nRemain):
            # generate a new random statepoint
            code = util.randomString(len(job.sp.goal))
            statepoint = dict(length=len(job.sp.goal),
                                  goal=job.sp.goal,
                                  code=code,
                                  seed=job.sp.seed,
                                  master=False)
            project.open_job(statepoint).init()
            lJob = project.open_job(statepoint)
            lJob.document.generation = gNum + 1
        lGeneration = project.find_jobs(filter={'master': False}, doc_filter={'generation': gNum+1})
        nRemain = len(sortList) - len(lGeneration)
    project.document.generation.n = gNum + 1
    # remove "old" jobs to keep the optimization fast
    oldJobs = project.find_jobs(filter={'master': False}, doc_filter={'generation': {'$lt': gNum-2}})
    for j in oldJobs:
        j.remove()

    stopTime = time.time()
    project.document.time[str(gNum)] = stopTime
    project.document.njobs[str(gNum)] = len(project.find_jobs())

if __name__ == "__main__":
    Project().main()
