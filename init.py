#!/usr/bin/env python
"""
Initialize the data space for the "Hello World!"
Genetic Optimization example.

Creates random initial state points and initializes
the associated job workspace directories
"""

import logging
import argparse
from hashlib import sha1

import signac
import numpy as np

def _calcCost(code, goal):
    """
    Calculate the cost of a given code by its
    distance from the goal using ASCII key
    codes
    """
    costCode = np.array([ord(i) for i in code])
    costGoal = np.array([ord(i) for i in goal])
    diffCost = int(np.power(np.sum(costCode - costGoal), 2))
    return diffCost

def randomString(length):
    """
    Return a random string of pre-defined characters
    of length
    """
    # 32 and 127 serve as bounds for displayable characters
    randArr = np.random.randint(low=32, high=127, size=length)
    code = "".join([chr(i) for i in randArr])
    return code

def main(n, seed):
    project = signac.init_project("HelloWorldGA")
    # create the master job
    goal = 'Hello, World!'
    statepoint = dict(master=True, goal=goal, seed=seed)
    project.open_job(statepoint).init()
    lJob = project.open_job(statepoint)
    lJob.document.generation = 0
    # Test the project document
    # project.document.generation = 0
    lDict = {'n': 0, 'members': None}
    project.document.generation = lDict
    project.document.time = dict()
    project.document.njobs = dict()
    # set the random seed
    np.random.seed(seed=seed)
    for i in range(n):
        # generate a random string
        # a length of 13 is the length of 'Hello, World!'
        length = len(goal)
        lCode = randomString(length)
        # cost of the code can't be part of the statepoint
        # I mean, technically from one point of view it
        # must be, but from another, it can't since it
        # would be part of the operation before creating a
        # new job, and the cost calculation should be part
        # of that process
        # lCost = _calcCost(lCode, goal)
        statepoint = dict(length=length,
                          goal=goal,
                          code=lCode,
                          seed=seed,
                          master=False)
        # create the job
        project.open_job(statepoint).init()
        lJob = project.open_job(statepoint)
        lJob.document.generation = 0
        # lJob.document.eligible = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize the data space.")
    parser.add_argument('psize',
        type=int,
        help="number of individuals in the population",)
    parser.add_argument("-s", "--seed", type=str,
        help="random seed to create the population")
    args = parser.parse_args()

    n = args.psize
    if args.seed:
        try:
            seed = int(args.seed)
        except:
            seed = int(sha1(args.seed.encode()).hexdigest(), 16) % (10 ** 8)
    else:
        seed = 42
    logging.basicConfig(level=logging.INFO)
    main(n, seed)
