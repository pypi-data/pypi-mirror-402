
# =============================================================================
# Intro
# =============================================================================

# This script shows how to use Erlang calculators in Python.
# See further examples and frequently asked questions at https://erlang.ccmath.com/faq

# =============================================================================
# Preliminary Steps:
# =============================================================================
import ERLANG

# A useful package for a test file:
import math
from tabulate import tabulate

# Tabulate and math are not necessary for the package itself.
# However, they are used in demo file for computational simplicity and good visualization.
# You can install them by: pip install tabulate and pip install math
# Or pip3 install tabulate and pip3 install math

# If you are an authenticated user, a calculation would give a numeric.
# If you are not authenticated, it will ask you to enter your user ID.
# If UID is not correct, you will receive an error.
# Otherwise, you will be authenticated.


# Function for rounding the results given decimals (used for simplicity, not required)
def round_list(result,decimals=2):
    if type(result) == str:
        if (result=="UID is not valid"):
            raise ValueError('UID is not valid!')
        else:
            return result
    if type(result) == float or type(result) == int:
        return round(result, decimals)
    elif type(result)==list and len(result)==1:
        return round(result[0], decimals)
    elif type(result)==list and len(result)>1:
        res=[]
        for item in result:
            res.append(round(item, decimals))
        return res

# Choose decimals to show:
decimals=2

# =============================================================================
# ERLANG C:
# The Erlang C model is a queuing system where:
# Customers arrive according to a Poisson process.
# Customers are served by a fixed number of single-skilled servers.
# All calls that find all servers busy wait in the queue until they get served.
# The calls are answered in order of arrival, thus longest-waiting call is served first.
# The Erlang C model is often used for single-skill call centers with only inbound calls.
# =============================================================================

# Inputs: 
Forecast = 4
AHT = 3
AWT = 0.333
# calc_option defines the type of calculations. (For computational simplicity, not required)
# Enter 0 for ASA and SL Calculation (1st column of the Excel sheet)
# Enter 1 for Agents (SL) Calculation (2nd column of the Excel sheet)
# Enter 2 for Agents (ASA) Calculation (3rd column of the Excel sheet)

calc_option=0

# =============================================================================
# Example:
# We would like to determine the service level and the average speed of answer.
# We have the following information:
# on average we have 240 calls per hour
# the average handling time is 3 minutes
# the acceptable waiting time is 20 seconds
# the number of agents is 14


# The first step is to transform the given data into units that are expressed in minutes.
# The arrival rate should be transformed in minutes:
# in this case there will be (240/60=) 4 calls per minute
# the acceptable waiting time will be (20/60=) 0.333 minutes
# Choose calc_option = 0

# The output of this computation is as follows:
# Average speed of answering a call is 0.72 minutes
# 61.42% of calls are answered within 20 seconds
# The agents are busy 85.71% of the time they are working
# =============================================================================
if calc_option==0:
    print('------ Erlang C for ASA and SL Calculation------')
    Agents = 14
    ASA = round_list(ERLANG.X.ASA(Forecast,AHT,Agents),decimals)
    SL = round_list(100*ERLANG.X.SLA(Forecast,AHT,Agents,AWT),decimals)
    Occupancy = round_list(100*ERLANG.X.OCCUPANCY(Forecast,AHT,Agents),decimals)
    Is_Input = ['Input','Input','Input','Input','Output','Output','Output']

elif calc_option==1:
    print('------ Erlang C for Agents (SL) Calculation------')
    SL = 80
    Agents = math.ceil(round_list(ERLANG.X.AGENTS.SLA(SL/100, Forecast, AHT, AWT),decimals))
    ASA = round_list(ERLANG.X.ASA(Forecast,AHT,Agents),decimals)
    Occupancy = round_list(100*ERLANG.X.OCCUPANCY(Forecast,AHT,Agents),decimals)
    Is_Input = ['Input','Input','Input','Output','Output','Input','Output']

elif calc_option==2:
    print('------ Erlang C for Agents (ASA) Calculation------')
    ASA = 0.333
    Agents = math.ceil(round_list(ERLANG.X.AGENTS.ASA(ASA, Forecast, AHT),decimals))
    SL = round_list(100*ERLANG.X.SLA(Forecast, AHT, Agents, AWT),decimals)
    Occupancy = round_list(100*ERLANG.X.OCCUPANCY(Forecast,AHT,Agents),decimals)
    Is_Input = ['Input','Input','Input','Output','Input','Output','Output']

col_names = ['Variable', 'Is_input', 'Value', 'Explanation']
erlang_c = [['Volume forecast', Is_Input[0], Forecast,' per time unit'],
         ['Average handling time ', Is_Input[1], AHT,'time units'],
         ['Acceptable waiting time', Is_Input[2], AWT,'time units'],
         ['Number of agents', Is_Input[3], Agents],
         ['Average speed of answer', Is_Input[4], ASA,'time units'],
         ['Service level', Is_Input[5], SL,'%'],
         ['Occupancy level', Is_Input[6], Occupancy, '%']]
print(tabulate(erlang_c, headers=col_names))

# =============================================================================
# ERLANG C: How to use arrays
# =============================================================================

# Let's consider ERLANG.X.ASA function for 3 cases:
case=1

# CASE 1: len(Forecast) = len(AHT)
if case==1:
    Forecast= [3.5, 3, 3, 2.5, 2.5]
    AHT= [2.8, 4.2, 4, 3.7, 4.5]
    # This will generate:
    # ERLANG.X.ASA(3.5, 2.8, Agents)
    # ERLANG.X.ASA(3, 4.2, Agents)
    # ERLANG.X.ASA(3, 4, Agents)
    # ERLANG.X.ASA(2.5, 3.7, Agents)
    # ERLANG.X.ASA(2.5, 4.5, Agents)

# CASE 2: len(Forecast) < len(AHT)
elif case==2:
    Forecast= [3,4]
    AHT= [5,5.1,5.2,5.3,4.5]
    # This will generate:
    # ERLANG.X.ASA(3, 5, Agents)
    # ERLANG.X.ASA(4, 5.1, Agents)
    # ERLANG.X.ASA(3, 5.2, Agents)
    # ERLANG.X.ASA(4, 5.3, Agents)
    # ERLANG.X.ASA(3, 4.5, Agents)

# CASE 3: len(Forecast) > len(AHT)
elif case==3:
    Forecast= [3,4,5,4,2]
    AHT= [3,2,2.5]
    # This will generate:
    # ERLANG.X.ASA(3, 3, Agents)
    # ERLANG.X.ASA(4, 2, Agents)
    # ERLANG.X.ASA(5, 2.5, Agents)
    # ERLANG.X.ASA(4, 3, Agents)
    # ERLANG.X.ASA(2, 2, Agents)

size = max(len(Forecast),len(AHT))
AWT = [0.333]*size
calc_option=0
# calc_option defines the type of calculations. (For computational simplicity, not required)
# Enter 0 for ASA and SL Calculation (1st column of the Excel sheet)
# Enter 1 for Agents (SL) Calculation (2nd column of the Excel sheet)
# Enter 2 for Agents (ASA) Calculation (3rd column of the Excel sheet)


#Outputs:
Values=[]
col_names = ['Variable', 'Is_input']
for i in range(size):
    Values.append(i+1)
    col_names.append('Value '+str(Values[i]))
col_names.append('Explanation')
erlang_c_array= [['Volume forecast', ' per time unit'],
                      ['Average handling time ', 'time units'],
                      ['Acceptable waiting time','time units'],
                      ['Number of agents'],
                      ['Average speed of answer', 'time units'],
                      ['Service level', '%'],
                      ['Occupancy level','%']]

if calc_option==0:
    # ASA and SL Calculation (1st column):
    print('\n------ Erlang C with Arrays of Size',size,'for ASA and SL Calculation','------')
    Agents = [14]*size
    ASA=round_list(ERLANG.X.ASA(Forecast, AHT, Agents),decimals)
    SL=ERLANG.X.SLA(Forecast, AHT, Agents, AWT)
    Occupancy=ERLANG.X.OCCUPANCY(Forecast, AHT, Agents)
    Is_Input = ['Input','Input','Input','Input','Output','Output','Output']
    SL = round_list([i * 100 for i in SL],decimals)

    Occupancy = round_list([i * 100 for i in Occupancy],decimals)
    variables = [Forecast, AHT, AWT,Agents, ASA, SL, Occupancy]
    for var in range(len(variables)):
        erlang_c_array[var].insert(1, Is_Input[var])
        for i in range(size):
            erlang_c_array[var].insert(2+i,variables[var][i])

elif calc_option==1:
    # Agents (SL) Calculation (2nd column):
    print('\n------ Erlang C with Arrays of Size', size, 'Agents (SL) Calculation', '------')
    SL = [0.8]*size
    Agents=round_list(ERLANG.X.AGENTS.SLA(SL, Forecast, AHT, AWT),0)
    ASA=round_list(ERLANG.X.ASA(Forecast, AHT, Agents),decimals)
    Occupancy=ERLANG.X.OCCUPANCY(Forecast, AHT, Agents)
    Is_Input = ['Input', 'Input', 'Input','Output', 'Output', 'Input',  'Output']
    SL = round_list([i * 100 for i in SL],decimals)
    Occupancy = round_list([i * 100 for i in Occupancy],decimals)
    variables = [Forecast, AHT, AWT, Agents, ASA, SL, Occupancy]
    for var in range(len(variables)):
        erlang_c_array[var].insert(1, Is_Input[var])
        for i in range(size):
            erlang_c_array[var].insert(2+i,variables[var][i])

elif calc_option==2:
    # Agents (ASA) Calculation (3rd column):
    print('\n------ Erlang C with Arrays of Size', size, 'Agents (ASA) Calculation', '------')
    ASA = [0.333]*size
    Agents=round_list(ERLANG.X.AGENTS.ASA(ASA, Forecast, AHT),0)
    SL=ERLANG.X.SLA(Forecast, AHT, Agents, AWT)
    Occupancy=ERLANG.X.OCCUPANCY(Forecast, AHT, Agents)
    Is_Input = ['Input','Input','Input','Output','Input','Output','Output']
    SL = round_list([i * 100 for i in SL],decimals)
    Occupancy = round_list([i * 100 for i in Occupancy],decimals)
    variables = [Forecast, AHT, AWT, Agents, ASA, SL, Occupancy]
    for var in range(len(variables)):
        erlang_c_array[var].insert(1, Is_Input[var])
        for i in range(size):
            erlang_c_array[var].insert(2+i,variables[var][i])

print(tabulate(erlang_c_array, headers=col_names))

# It is also possible to use arrays in Erlang X, Chat, and Blending calculators, similarly.

# =============================================================================
# ERLANG X:
# The Erlang X model is a queueing system with the further features:
# Queued customers are impatient and abandons the queue after an exponentially distributed amount of time.
# Call is not queued but disconnected due to a finite number of lines.
# Blocking avoids long waiting time and therefore bad service by limiting
# the number of customers allowed to be in the system at any time.
# Abandoned customers may redial with a certain probability.
# The Erlang X model gives a better estimate than the Erlang C model by involving
# customer behavior in the queueing system, considering patience, abandonments, and redials.
# =============================================================================

# Inputs: 
Forecast = 4
AHT = 3
Patience = 1
AWT = 0.333
Lines = 100


# calc_option defines the type of calculations. (For computational simplicity, not required)
# Enter 0 for ASA and SL Calculation (1st column of the Excel sheet)
# Enter 1 for Agents (SL) Calculation (2nd column of the Excel sheet)
# Enter 2 for Agents (ASA) Calculation (3rd column of the Excel sheet)
# Enter 3 for Agents (Occupancy) Calculation (4th column of the Excel sheet)

calc_option=0

# =============================================================================
# Example:
# We would like to determine the service level and the average speed of answer.
# We have the following information:
# on average we have 240 calls per hour
# the average handling time is 3 minutes
# the average patience of callers is 1 minute
# the acceptable waiting time is 20 seconds
# the number of lines is 100
# the number of agents is 14

# The first step is to transform the given data into units that are expressed in minutes.
# The arrival rate should be transformed in minutes:
# in this case there will be (240/60=) 4 calls per minute
# the acceptable waiting time will be (20/60=) 0.333 minutes
# Choose calc_option = 0

# The output of this computation is as follows:
# Average speed of answering a call is 0.1 minutes
# 87.97% of calls are answered within 20 seconds
# 7.43% of customers abandon while waiting in the queue
# 0% of calls are blocked, all are accepted to the queue
# The agents are busy 79.34% of the time they are working
# =============================================================================

if calc_option==0:
    # ASA and SL Calculation (1st column):
    print('\n------ Erlang X for ASA and SL Calculation------')
    Agents = 14
    ASA = round_list(ERLANG.X.ASA(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    SL = round_list(100*ERLANG.X.SLA(Forecast, AHT, Agents, AWT, Lines, Patience, 0),decimals)
    Abandon = round_list(100*ERLANG.X.ABANDON(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    Blocking = round_list(100 * ERLANG.X.BLOCKING(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Occupancy = round_list(100 * ERLANG.X.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output', 'Output', 'Output']

elif calc_option==1:
    # Agents (SL) Calculation (2nd column):
    print('\n------ Erlang X for Agents (SL) Calculation------')
    SL = 80
    Agents = math.ceil(ERLANG.X.AGENTS.SLA(SL/100, Forecast, AHT, AWT, Lines, Patience, 0))
    ASA = round_list(ERLANG.X.ASA(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    Abandon = round_list(100*ERLANG.X.ABANDON(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    Blocking = round_list(100 * ERLANG.X.BLOCKING(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Occupancy = round_list(100 * ERLANG.X.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Input', 'Output', 'Output', 'Output']

elif calc_option==2:
    # Agents (ASA) Calculation (3rd column):
    print('\n------ Erlang X for Agents (Abandonment) Calculation------')
    Abandon = 5
    Agents = math.ceil(ERLANG.X.AGENTS.ABANDON(Abandon/100, Forecast, AHT, Lines, Patience, 0))
    ASA = round_list(ERLANG.X.ASA(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    SL = round_list(100*ERLANG.X.SLA(Forecast, AHT, Agents, AWT, Lines, Patience, 0),decimals)
    Blocking = round_list(100 * ERLANG.X.BLOCKING(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Occupancy = round_list(100 * ERLANG.X.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output', 'Input', 'Output', 'Output']

elif calc_option==3:
    # Agents (Occupancy) Calculation (4rd column):
    print('\n------ Erlang X for Agents (Occupancy) Calculation------')
    Occupancy = 70
    Agents = math.ceil(ERLANG.X.AGENTS.OCCUPANCY(Occupancy/100, Forecast, AHT, Lines, Patience, 0))
    ASA = round_list(ERLANG.X.ASA(Forecast, AHT, Agents, Lines, Patience, 0),decimals)
    SL = round_list(100*ERLANG.X.SLA(Forecast, AHT, Agents, AWT, Lines, Patience, 0),decimals)
    Abandon = round_list(100 * ERLANG.X.ABANDON(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Blocking = round_list(100 * ERLANG.X.BLOCKING(Forecast, AHT, Agents, Lines, Patience, 0), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output', 'Output', 'Output', 'Input']



col_names = ['Variable', 'Is_input', 'Value', 'Explanation']
erlang_x = [['Volume forecast', Is_Input[0], Forecast,' per time unit'],
         ['Average handling time', Is_Input[1], AHT,'time units'],
         ['Average patience of callers', Is_Input[2], Patience,'time units'],
         ['Acceptable waiting time', Is_Input[3], AWT,'time units'],
         ['Number of lines', Is_Input[4], Lines],
         ['Number of agents', Is_Input[5], Agents],
         ['Average speed of answer', Is_Input[6], ASA,'time units'],
         ['Service level', Is_Input[7], SL,'%'],
         ['Abandonments', Is_Input[8], Abandon,'%'],
         ['Blocked calls', Is_Input[9], Blocking,'%'],
         ['Occupancy level', Is_Input[10], Occupancy, '%']]
print(tabulate(erlang_x, headers=col_names))



# =============================================================================
# ERLANG BLENDING:
# The Erlang Blending model considers that agents can work on different types of calls: inbound and outbound.
# It is assumed that there is an infinite amount of outbound calls to be done.
# When an agent finishes a call, they will always take the longest waiting inbound call from the queue, if there is any.
# In case the queue with inbound calls is empty, a decision has to be made:
# 1) Either the agent takes an outbound call
# 2) Or remains idle to be available for the next arriving inbound call.
# This decision is modeled using a threshold.
# Let threshold value be x (x < agents):
# An available agent may take an outbound call only when the x agents are left idle.
# =============================================================================

# Inputs: 
Forecast = 4
AHT = 3
Agents = 16
AWT = 0.333


# calc_option defines the type of calculations. (For computational simplicity, not required)
# Enter 0 for ASA, SL, Occupancy, and Outbound Call Calculation given Threshold input
# Enter 1 for ASA, Threshold, Occupancy, and Outbound Call Calculation given Service Level input
calc_option=0

# =============================================================================
# Example:
# We would like to determine the service level and the average speed of answer.
# We have the following information:
# on average we have 240 calls per hour
# the average handling time is 3 minutes
# the average patience of callers is 1 minute
# the acceptable waiting time is 20 seconds
# the number of agents is 16
# the threshold value for agents is 2
# This means that an outbound call can only be started when the 3rd agent becomes idle
# Note that this does not mean that 3 agents are always idle, they will still work on inbound calls.

# The first step is to transform the given data into units that are expressed in minutes.
# The arrival rate should be transformed in minutes:
# in this case there will be (240/60=) 4 calls per minute
# the acceptable waiting time will be (20/60=) 0.333 minutes
# Choose calc_option = 0

# The output of this computation is as follows:
# Average speed of answering a call is 0.43 minutes
# 63.34% of calls are answered within 20 seconds
# % of customers abandon while waiting in the queue
# The agents are busy 95.83% of the time they are working
# 1.11 among 4 calls are outbound calls per minute
# =============================================================================

if calc_option==0:
    print('\n------ Erlang Blending for ASA and SL Calculation given Threshold------')
    Threshold = 2
    ASA = round_list(ERLANG.BL.ASA(Forecast, AHT, Agents, Threshold),decimals)
    SL = round_list(100*ERLANG.BL.SLA(Forecast, AHT, Agents, AWT, Threshold),decimals)
    Occupancy = round_list(100*ERLANG.BL.OCCUPANCY(Forecast, AHT, Agents, Threshold),decimals)
    Outbound = round_list(ERLANG.BL.OUTBOUND(Forecast, AHT, Agents, Threshold),decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output', 'Output']
    
elif calc_option==1:
    print('\n------ Erlang Blending for ASA and Threshold Calculation given SL------')
    SL=80
    ASA =round_list(ERLANG.BL.ASA.SLA(Forecast, AHT, Agents, SL/100, AWT),decimals)
    Threshold = round_list(ERLANG.BL.THRESHOLD(Forecast, AHT, Agents, SL/100, AWT),decimals)
    Occupancy =round_list(100*ERLANG.BL.OCCUPANCY.SLA(Forecast, AHT, Agents, SL/100, AWT),decimals)
    Outbound = round_list(ERLANG.BL.OUTBOUND.SLA(Forecast, AHT, Agents, SL/100, AWT),decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Input', 'Output', 'Output']
    
col_names = ['Variable', 'Is_input', 'Value', 'Explanation']
erlang_blending = [['Volume forecast', Is_Input[0], Forecast,' per time unit'],
         ['Average handling time ', Is_Input[1], AHT,'time units'],
         ['Acceptable waiting time', Is_Input[2], AWT,'time units'],
         ['Number of agents', Is_Input[3], Agents],
         ['Threshold', Is_Input[4], Threshold],
         ['Average speed of answer', Is_Input[5], ASA,'time units'],
         ['Service level', Is_Input[6], SL,'%'],
         ['Occupancy level', Is_Input[7], Occupancy, '%'],
         ['Outbound calls', Is_Input[8], Outbound, ' per time unit']]
print(tabulate(erlang_blending, headers=col_names))

# =============================================================================
# ERLANG CHAT:
# The Erlang Chat model is the extension of Erlang X model:
# Now, agents can now handle multiple chats at the same time.
# Handling multiple chats in parallel is often more efficient than handling each chat individually, one after the other.
# On the other hand, the time spent on a certain chat could increase when working on multiple chats at the same time.
# =============================================================================

# Inputs: 
Forecast = 4
AHT = [3,3.5,4]
Patience = 1
AWT = 0.333
Lines = 100

# calc_option defines the type of calculations. (For computational simplicity, not required)
# Enter 0 for ASA and SL Calculation (1st column of the Excel sheet)
# Enter 1 for Agents (SL) Calculation (2nd column of the Excel sheet)
# Enter 2 for Agents (Abandonment) Calculation (3rd column of the Excel sheet)
# Enter 3 for Agents (Occupancy) Calculation (4th column of the Excel sheet)
calc_option=0

# =============================================================================
# Example:
# We would like to determine the service level and the average speed of answer.
# We have the following information:
# on average we have 240 incoming chats per hour
# agents have 3 parallel chats to handle at the same time
# the average handling times of chats are 3, 3.5, and 4 minutes.
# the average patience of customers is 1 minute
# the acceptable waiting time is 20 seconds
# the number of lines is 100
# the number of agents is 5

# The first step is to transform the given data into units that are expressed in minutes.
# The arrival rate should be transformed in minutes:
# in this case there will be (240/60=) 4 chats per minute
# the acceptable waiting time will be (20/60=) 0.333 minutes
# Choose calc_option=0

# The output of this computation is as follows:
# Average speed of answering a customer is 0.22 minutes
# 75.44% of customers are answered within 20 seconds
# 15.44% of customers abandon while waiting to be answered
# The agents are busy 86.78% of the time they are working
# =============================================================================

if calc_option==0:
    # ASA and SL Calculation (1st column):
    print('\n------ Erlang Chat for ASA and SL Calculation------')
    Agents = 5
    ASA = round_list(ERLANG.CHAT.ASA(Forecast, AHT, Agents, Lines, Patience),decimals)
    SL = round_list(100*ERLANG.CHAT.SLA(Forecast, AHT, Agents, AWT, Lines, Patience),decimals)
    Abandon = round_list(100 * ERLANG.CHAT.ABANDON(Forecast, AHT, Agents, Lines, Patience), decimals)
    Occupancy = round_list(100 * ERLANG.CHAT.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output','Output','Output']

elif calc_option==1:
    # Agents (SL) Calculation (2nd column):
    print('\n------ Erlang Chat for Agents (SL) Calculation------')
    SL = 80
    Agents = round_list(ERLANG.CHAT.AGENTS.SLA(SL/100, Forecast, AHT, AWT, Lines, Patience),0)
    ASA = round_list(ERLANG.CHAT.ASA(Forecast, AHT, Agents, Lines, Patience),decimals)
    Abandon = round_list(100 * ERLANG.CHAT.ABANDON(Forecast, AHT, Agents, Lines, Patience), decimals)
    Occupancy = round_list(100 * ERLANG.CHAT.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Input','Output','Output']

elif calc_option==2:
    # Agents (Abandonment) Calculation (2nd column):
    print('\n------ Erlang Chat for Agents (Abandonment) Calculation------')
    Abandon = 5
    Agents = round_list(ERLANG.CHAT.AGENTS.ABANDON(Abandon/100, Forecast, AHT, Lines, Patience),0)
    ASA = round_list(ERLANG.CHAT.ASA(Forecast, AHT, Agents, Lines, Patience),decimals)
    SL = round_list(100 * ERLANG.CHAT.SLA(Forecast, AHT, Agents, AWT, Lines, Patience), decimals)
    Occupancy = round_list(100 * ERLANG.CHAT.OCCUPANCY(Forecast, AHT, Agents, Lines, Patience), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output','Input','Output']

elif calc_option==3:
    # Agents (Occupancy) Calculation (3nd column):
    print('\n------ Erlang Chat for Agents (Occupancy) Calculation------')
    Occupancy = 80
    Agents = round_list(ERLANG.CHAT.AGENTS.OCCUPANCY(Occupancy/100, Forecast, AHT, Lines, Patience),0)
    ASA = round_list(ERLANG.CHAT.ASA(Forecast, AHT, Agents, Lines, Patience),decimals)
    SL = round_list(100 * ERLANG.CHAT.SLA(Forecast, AHT, Agents, AWT, Lines, Patience), decimals)
    Abandon = round_list(100 * ERLANG.CHAT.ABANDON(Forecast, AHT, Agents, Lines, Patience), decimals)
    Is_Input = ['Input', 'Input', 'Input', 'Input', 'Input', 'Output', 'Output', 'Output','Output','Input']


col_names = ['Variable', 'Is_input', 'Value', 'Explanation']
erlang_chat = [['Volume forecast', Is_Input[0], Forecast,' per time unit'],
         ['Average handling time', Is_Input[1], AHT,'time units'],
         ['Average patience of customers', Is_Input[2], Patience,'time units'],
         ['Acceptable waiting time', Is_Input[3], AWT,'time units'],
         ['Number of lines', Is_Input[4], Lines],
         ['Number of agents', Is_Input[5], Agents],
         ['Average speed of answer', Is_Input[6], ASA,'time units'],
         ['Service level', Is_Input[7], SL,'%'],
         ['Abandonments', Is_Input[8], Abandon,'%'],
         ['Occupancy level', Is_Input[9], Occupancy,'%']]
print(tabulate(erlang_chat, headers=col_names))

# =============================================================================
# How to use arrays in Erlang Chat in calc_option 0:
# =============================================================================

print('\n------ Erlang Chat Calculations with Arrays for Agents (SL) Calculation------')
# Let us define forecast and agents arrays:
Forecast = [4,4,12,3,1]
Agents = [4,5]

# AHT array denotes the average handling time of one agent with parallel operations:
AHT = [3,3.5,4]
# Note that the length of the AHT parameter for Chat does not count 
# toward finding the parameter with the longest length.

Patience = 1
AWT = 0.333
Lines = 100

print('INPUTS:')
print("Forecast:",Forecast)
print("Average handling time:",AHT)
print("Patience:",Patience)
print("Average waiting time:",AWT)
print("Lines:",Lines)

# This parameters will generate the following for ASA function:
# print(ERLANG.CHAT.ASA([4,4,12,3,1], AHT, [4,5], Lines, Patience))

# Note that this is equivalent to the following functions:
# print(ERLANG.CHAT.ASA(4, AHT, 4, Lines, Patience))
# print(ERLANG.CHAT.ASA(4, AHT, 5, Lines, Patience))
# print(ERLANG.CHAT.ASA(12, AHT, 4, Lines, Patience))
# print(ERLANG.CHAT.ASA(3, AHT, 5, Lines, Patience))
# print(ERLANG.CHAT.ASA(1, AHT, 4, Lines, Patience))

ASA = round_list(ERLANG.CHAT.ASA(Forecast, AHT, Agents, Lines, Patience),decimals)
SL = round_list(ERLANG.CHAT.SLA(Forecast, AHT, Agents, AWT, Lines, Patience),decimals)
print("Number of agents:",Agents)
print('OUTPUTS:')
print("Average speed of answer:",ASA)
print("Service level:",SL)
