"""
Avoiding barren plateaus with local cost functions
==========
.. meta::
    :property="og:description": Local cost functions are cost formulations for variational quantum computing that are more robust to barren plateaus, and noise.
    :property="og:image": ../demonstrations/local_cost_functions/Cerezo_et_al_local_cost_functions.png
    
Barren Plateaus
---------------

Barren plateaus are large regions of the cost function's parameter space
where the variance of the gradient is almost 0; or, put another way, the
cost function landscape is flat. This means that a variational circuit
initialized in one of these areas will be untrainable using any gradient based
algorithm.



In `"Cost-Function-Dependent Barren Plateaus in Shallow Quantum Neural
Networks" <https://arxiv.org/abs/2001.00550>`__ Cerezo et al. demonstrate the
idea that the barren plateau
phenomenon can be avoided by using cost functions that only have
information from part of the circuit. These *local* cost functions are
more robust to noise, and have more well-behaved gradients with no
plateaus for shallow circuits.


.. figure:: ../demonstrations/local_cost_functions/Cerezo_et_al_local_cost_functions.png
   :align: center
   :width: 50%
   
In a quick explanation, a global cost function is the type that is traditionally used.
Information from the entire measurement is used to analyze the result of the 
circuit, and a cost function is calculated from this to quantify the circuits 
performance. A local cost function only considers information from a few qubits, 
and attempts to analyze the behavior of the entire circuit from this limited scope.


Cerezo et al. also handily prove that these local cost functions are bounded by the 
global ones, i.e. if a global cost function is formulated in the manner discribed
by Cerezo, then its corrisponding local cost function will always be 
less than or equal to the global.

Imports
--------------

In this notebook, we investigate the effect of barren plateaus in
variational quantum algorithms, and how they can be mitigated using
local cost functions.
"""


import pennylane as qml
from pennylane import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LinearLocator, FormatStrFormatter


######################################################################
# Visualizing the problem
# --------------
#
# To start, lets look at the task of learning the identity gate
# across multiple qubits. This will help us visualize the problem and get
# a sense of what is happening in the cost landscape.
#
# First we define a number of wires we want to train on. The work by
# Cerezo et al. shows that circuits are trainible under certain regimes, so
# how many qubits we train on will effect our results.

wires = 6
dev = qml.device("default.qubit", wires=wires, shots=10000, analytic=False)


######################################################################
# Next, we want to define our QNodes, containing our ansatz. For this
# simple example, an ansatz that works well is simply a rotation along X,
# and a rotation along Y, repeated across all the qubits.
#
# We will also define our cost functions here. Since we are trying to
# learn the identity gate, a natural cost function is the probablity of measuring the 
# zero state.
#
# .. math:: C = 1-p_{|0\rangle}
#
# We will apply this across all qubits for our global cost function, i.e.:
#
# .. math:: C_{G} = 1-p_{|00 \ldots 0\rangle}
#
# and only on one qubit for our local cost function:
#
# .. math:: C_{L} = 1-p_{|0>}.
#
# To implement this, we will define a separate QNode for the local cost
# function and the global cost function.
#


def global_cost_simple(rotations):
    for i in range(wires):
        qml.RX(rotations[0][i], wires=i)
        qml.RY(rotations[1][i], wires=i)
    for i in range(wires-1):
        qml.CNOT(wires=[i,i+1])    
    return qml.probs(wires=range(wires))


def local_cost_simple(rotations):
    for i in range(wires):
        qml.RX(rotations[0][i], wires=i)
        qml.RY(rotations[1][i], wires=i)
    for i in range(wires-1):
        qml.CNOT(wires=[i,i+1])    
    return qml.probs(wires=[0])


def cost_local(rotations):
    return 1 - local_circuit(rotations)[0]


def cost_global(rotations):
    return 1 - global_circuit(rotations)[0]


global_circuit = qml.QNode(global_cost_simple, dev)

local_circuit = qml.QNode(local_cost_simple, dev)


######################################################################
# To analyze each of the circuits, we provide some random initial
# parameters for each rotation
#

RX = np.random.uniform(low=-np.pi, high=np.pi)
RY = np.random.uniform(low=-np.pi, high=np.pi)
rotations = [[RX for i in range(wires)], [RY for i in range(wires)]]


######################################################################
# And look at the results:
#

print("Global Cost: {: .7f}".format(cost_global(rotations)))
print("Local Cost: {: .7f}".format(cost_local(rotations)))
print("--- Global Circuit ---")
print(global_circuit.draw())
print("--- Local Circuit")
print(local_circuit.draw())


######################################################################
# With this simple example, we can visualize the cost function, and see
# the barren plateau effect graphically. Although there are 2n (where n is the 
# number of qubits) parameters, in order to make the cost landscape plot-able 
# we must constrain ourselves. We will assume that all the X rotations are the 
# same, and all the Y rotations are the same.

X = np.arange(-np.pi, np.pi, 1)
Y = np.arange(-np.pi, np.pi, 1)
X, Y = np.meshgrid(X, Y)

local_Z = []
global_Z = []
local_z = []
global_z = []

X = np.arange(-np.pi, np.pi, 0.25)
Y = np.arange(-np.pi, np.pi, 0.25)
X, Y = np.meshgrid(X, Y)

for x in X[0, :]:
    for y in Y[:, 0]:
        rotations = [[x for i in range(wires)], [y for i in range(wires)]]
        local_z.append(cost_local(rotations))
        global_z.append(cost_global(rotations))
    local_Z.append(local_z)
    global_Z.append(global_z)
    local_z = []
    global_z = []

local_Z = np.asarray(local_Z)
global_Z = np.asarray(global_Z)


######################################################################
# Firstly, we look at the global cost function. When plotting the cost
# function across 6 qubits, much of the cost landscape is flat, and
# difficult to train (even with a circuit depth of only 2!). This effect
# will worsen as the number of qubits increases.
#

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, global_Z, cmap="viridis", linewidth=0, antialiased=False)
ax.set_zlim(0, 1)
ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter(FormatStrFormatter("%.02f"))
plt.show()


######################################################################
# However, when we change to the local cost function, the cost landscape
# becomes much more trainable.
#

fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(X, Y, local_Z, cmap="viridis", linewidth=0, antialiased=False)
ax.set_zlim(0, 1)
ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter(FormatStrFormatter("%.02f"))
plt.show()


######################################################################
# Those are some nice pictures, but how do they reflect actual
# trainability? Lets try training both the local, and global cost
# functions. Because we have a visualization of the total cost landscape,
# lets pick a point to exaggerate the problem. The worst point in the
# landscape is :math:`(\pi,0)`, so let's use that.
#

rotations = [[3 for i in range(wires)], [0 for i in range(wires)]]
opt = qml.GradientDescentOptimizer(stepsize=0.2)
steps = 100
params_global = rotations
for i in range(steps):
    # update the circuit parameters
    params_global = opt.step(cost_global, params_global)

    if (i + 1) % 1 == 0:
        print("Cost after step {:5d}: {: .7f}".format(i + 1, cost_global(params_global)))
    if cost_global(params_global) < 0.1:
        break
print(global_circuit.draw())


######################################################################
# After 100 steps, the cost function is still exactly 1. Clearly we are in
# an untrainable area. Now, lets limit the ourselves to the local cost
# function and see how it performs. 
#

rotations = [[3.0 for i in range(wires)], [0 for i in range(wires)]]
opt = qml.GradientDescentOptimizer(stepsize=0.2)
steps = 100
params_local = rotations
for i in range(steps):
    # update the circuit parameters
    params_local = opt.step(cost_local, params_local)

    if (i + 1) % 5 == 0:
        print("Cost after step {:5d}: {: .7f}".format(i + 1, cost_local(params_local)))
    if cost_local(params_local) < 0.05:
        break
print(local_circuit.draw())


######################################################################
# It trained! And much faster than the global case. However, we know our
# local cost function is bounded by the global one, but just how much
# have we trained it?
#

cost_global(params_local)


######################################################################
# Interestingly, the global cost function is still 1. If we trained the
# local cost function, why hasnt the global cost function changed?
#
# The answer is that we have trained the global cost a *little bit*, but
# not enough to see a change with only 10000 shots. To see the effect,
# we'll need to increase the number of shots to an unreasonable amount.
# Instead making the backend analytic gives us the exact
# representation.
#

dev.analytic = True
global_circuit = qml.QNode(global_cost_simple, dev)
print(
    "Current cost: "
    + str(cost_global(params_local))
    + ". Initial cost: "
    + str(cost_global([[3.0 for i in range(wires)], [0 for i in range(wires)]]))
    + ". Difference: "
    + str(
        cost_global([[3.0 for i in range(wires)], [0 for i in range(wires)]])
        - cost_global(params_local)
    )
)


######################################################################
# Our circuit has definitely been trained, but not a useful amount. If we
# attempt to use this circuit, it would act the same as if we never trained at all.
# Furthermore, if we now attempt to train the global cost function, we are
# still firmly in the plateau region. In order to fully train the global
# circuit, we will need to increase the locality gradually as we train.
#


def tunable_cost_simple(rotations):
    for i in range(wires):
        qml.RX(rotations[0][i], wires=i)
        qml.RY(rotations[1][i], wires=i)
    for i in range(wires-1):
        qml.CNOT(wires=[i,i+1])
    return qml.probs(range(locality))


def cost_tunable(rotations):
    # result = circuit(rotations)
    # return sum(abs(result[i]) for i in range(wires))
    return 1 - tunable_circuit(rotations)[0]


dev.analytic = False
tunable_circuit = qml.QNode(tunable_cost_simple, dev)
locality = 2
params_tunable = params_local
print(cost_tunable(params_tunable))
print(tunable_circuit.draw())

locality = 2
opt = qml.GradientDescentOptimizer(stepsize=0.1)
steps = 600
for i in range(steps):
    # update the circuit parameters
    params_tunable = opt.step(cost_tunable, params_tunable)

    runCost = cost_tunable(params_tunable)
    if (i + 1) % 10 == 0:
        print(
            "Cost after step {:5d}: {: .7f}".format(i + 1, runCost) + ". Locality: " + str(locality)
        )

    if runCost < 0.1 and locality < wires:
        print("---Switching Locality---")
        locality += 1
        continue
    elif runCost < 0.1 and locality >= wires:
        break
print(tunable_circuit.draw())


######################################################################
# A more thorough analysis.
# --------------

# Now the circuit can be trained, even though we started from a place
# where the global function has a barren plateau. The significance of this
# is that we can now train from every starting location in this example.
#
# But, how often does this problem occur? If we wanted to train this
# circuit from a random starting point, how often would we be stuck in a
# plateau? To investigate this, let's attempt to train the global cost
# function using random starting positions and count how many times we run
# into a barren plateau.
#
# Let's use a number of qubits we are more likely to use in a real variational 
# circuit: n=10. We will say that after
# 400 steps, any run with a cost function of less than 0.9 (chosen
# arbitrarily) will probably be trainable given more time. Any run with a
# greater cost function will probably be in a plateau.
#
# This may take up to 15 mins.
#

samples = 10
plateau = 0
trained = 0
opt = qml.GradientDescentOptimizer(stepsize=0.2)
steps = 400
wires = 10

dev = qml.device("default.qubit", wires=wires, shots=10000, analytic=False)
global_circuit = qml.QNode(global_cost_simple, dev)

for runs in range(samples):
    print("--- New run! ---")
    has_been_trained = False
    params_global = [
        [np.random.uniform(-np.pi, np.pi) for i in range(wires)],
        [np.random.uniform(-np.pi, np.pi) for i in range(wires)],
    ]
    for i in range(steps):
        # update the circuit parameters
        params_global = opt.step(cost_global, params_global)

        if (i + 1) % 20 == 0:
            print("Cost after step {:5d}: {: .7f}".format(i + 1, cost_global(params_global)))
        if cost_global(params_global) < 0.9:
            has_been_trained = True
            break
    if has_been_trained:
        trained = trained + 1
    else:
        plateau = plateau + 1
    print("Trained: {:5d}".format(trained))
    print("Plateau'd: {:5d}".format(plateau))


samples = 10
plateau = 0
trained = 0
opt = qml.GradientDescentOptimizer(stepsize=0.2)
steps = 400
wires = 10

dev = qml.device("default.qubit", wires=wires, shots=10000, analytic=False)
tunable_circuit = qml.QNode(tunable_cost_simple, dev)

for runs in range(samples):
    locality = 1
    print("--- New run! ---")
    has_been_trained = False
    params_tunable = [
        [np.random.uniform(-np.pi, np.pi) for i in range(wires)],
        [np.random.uniform(-np.pi, np.pi) for i in range(wires)],
    ]
    for i in range(steps):
        # update the circuit parameters
        params_tunable = opt.step(cost_tunable, params_tunable)

        runCost = cost_tunable(params_tunable)
        if (i + 1) % 10 == 0:
            print(
                "Cost after step {:5d}: {: .7f}".format(i + 1, runCost)
                + ". Locality: "
                + str(locality)
            )

        if runCost < 0.1 and locality < wires:
            print("---Switching Locality---")
            locality += 1
            continue
        elif runCost < 0.1 and locality >= wires:
            trained = trained + 1
            has_been_trained = True
            break
    if not has_been_trained:
        plateau = plateau + 1
    print("Trained: {:5d}".format(trained))
    print("Plateau'd: {:5d}".format(plateau))


######################################################################
# In the global case, anywhere between 70-80% of starting positions are
# untrainable, a significant number. It is likely as the complexity of our
# ansatz, and the number of qubits increases, this factor will increase.
#
# Comparing that to our local cost function, every single area trained,
# and most even trained in less time. While these examples are simple,
# this local-vs-global cost behavior has been shown to extend to more
# complex problems.
