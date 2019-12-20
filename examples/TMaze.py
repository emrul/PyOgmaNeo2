import pyogmaneo
from pyogmaneo import PyInt3
import numpy as np

# T-Maze example
# Simple prints the result of a simple T-Maze memory test environment. The more it prints just "Correct", the better it is doing.

cs = pyogmaneo.PyComputeSystem("cpu", 1234, 0) # First CPU device
prog = pyogmaneo.PyComputeProgram(cs, "../../OgmaNeo2/resources/neoKernels.cl")

hlds = []

# First layer description
fld = pyogmaneo.PyFirstLayerDesc()

fld._hiddenSize = pyogmaneo.PyInt3(4, 4, 16)
fld._ffRadius = 4 # Feed forward radius
fld._aRadius = 4 # Radius of action layers
fld._temporalHorizon = 4 # 4 timestep memory window. _ticksPerUpdate is always 1 for the first layer, so it is not set here
fld._historyCapacity = 32 # Reward backup horizon

# Other (higher) layer descriptions
for i in range(3): # 3 layers gives us 2^3=8 timesteps of memory
    ld = pyogmaneo.PyHigherLayerDesc()
    ld._hiddenSize = pyogmaneo.PyInt3(4, 4, 16)
    ld._ffRadius = 4 # Feed forward radius
    ld._pRadius = 4 # Prediction radius
    ld._temporalHorizon = 4 # 4 timestep memory window
    ld._ticksPerUpdate = 2 # 2 timestep striding (doubling time window every layer)

    hlds.append(ld)

h = pyogmaneo.PyHierarchy(cs, prog, [ PyInt3(1, 1, 4), PyInt3(1, 1, 3) ], [ pyogmaneo._inputTypeNone, pyogmaneo._inputTypeAct ], fld, hlds)

# Buffers for holding inputs and actions
inBuf = pyogmaneo.PyIntBuffer(cs, 1)
aBuf = pyogmaneo.PyIntBuffer(cs, 1)

# Configure action layer
h.setAAlpha(1, 0.05) # Value learning rate
h.setABeta(1, 0.1) # Action learning rate
h.setAGamma(1, 0.95) # Discount factor

reward = 0.0

act = 2

for i_episode in range(10000):
    mazeLen = 6 # 6-step maze

    side = int(np.random.rand() < 0.5) # Randomly choose the side the reward is on

    # Show signal
    inBuf.write(cs, [ side ])
    aBuf.write(cs, [ act ])

    h.step(cs, [ inBuf, aBuf ], reward, True)

    act = h.getActionCs(1).read(cs)[0] # Retrieve action

    # Go through tunnel
    for i in range(mazeLen):
        if act != 2: # If not taking forward action when in the beginning of the maze (tunnel)
            reward = -0.5

            print("Mistake") # Mistake while going down the tunnel
        else:
            reward = 0.0

        see = 2

        # Indicate that end of tunnel has been reached
        if i == mazeLen - 1:
            see = 3

        inBuf.write(cs, [ see ])
        aBuf.write(cs, [ act ])

        h.step(cs, [ inBuf, aBuf ], reward, True)

        act = h.getActionCs(1).read(cs)[0] # Retrieve action

    if act == side:
        reward = 1.0
        print("Correct")
    else:
        reward = -1.0
        print("Incorrect")

    act = side

    

    
