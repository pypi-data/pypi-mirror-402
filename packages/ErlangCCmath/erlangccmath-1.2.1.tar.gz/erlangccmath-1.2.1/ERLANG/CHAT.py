from ERLANG.settings import output
from ERLANG.settings import request
# =============================================================================
# ERLANG CHAT FUNCTIONS
# In the model for chats, the distinguishing feature is that agents can handle 
# multiple chats in parallel.
# =============================================================================
    
class SLA():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : list
        The Average Handling Time of a call. (AHT > 0). The difference between 
        this and the previous AHT parameter is that the AHT should be a range 
        of cells instead of a single number. The number of elements in the range
        determines the maximum number of concurrent chats that an agent can do. 
        This parameter is exclusively used in the Chat functions.
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Awt : float
        The Acceptable Waiting Time is the maximum allowed waiting time.
        Customers that wait shorter than the Awt have received, per definition,
        a good service. The service level is defined as the percentage of 
        customers that are served within the Awt. The time unit is the same as 
        the others and, hence, is not necessarily in seconds! (Awt ≥ 0)
    Lines : int
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
        Note: setting a default of 5* your top interval arrival # is good 
        practice, but remember it’s really about the capacity your company has 
        bought from the telephony provider.
    Patience : float
        The average time a customer is willing to wait in the queue. A simple 
        estimator for the patience is calculated by dividing the total waiting 
        time (including the waiting times of the abandoned customers) by the 
        number of abandonments. It is important to filter out extreme values 
        in advance. (Patience ≥ 0)
       
    Returns
    -------
    float
        The expected service level.
    """
   
    def __new__(cls,Forecast:float,AHT:list,Agents:float,Awt:float,Lines:int,Patience:float):
         Parallel=int(len(AHT))
         output['Parallel']=Parallel
         output['function']='serviceLevelErlangChat'
         for i in SLA.__new__.__annotations__:
             output[i]=locals()[i]
         return request(output)

class AGENTS:
     
    class SLA():
        """
        Parameters
        ----------
        SL : float
            The expected Service Level of an arbitrary non-blocked customer. (0 < SL < 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : list
            The Average Handling Time of a call. (AHT > 0). The difference between 
            this and the previous AHT parameter is that the AHT should be a range 
            of cells instead of a single number. The number of elements in the range
            determines the maximum number of concurrent chats that an agent can do. 
            This parameter is exclusively used in the Chat functions.
        Agents : float
            Represents the number of agents; it can be real. (Agents ≥ 0)
        Awt : float
            The Acceptable Waiting Time is the maximum allowed waiting time.
            Customers that wait shorter than the Awt have received, per definition,
            a good service. The service level is defined as the percentage of 
            customers that are served within the Awt. The time unit is the same as 
            the others and, hence, is not necessarily in seconds! (Awt ≥ 0)
        Lines : int
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
            Note: setting a default of 5* your top interval arrival # is good 
            practice, but remember it’s really about the capacity your company has 
            bought from the telephony provider.
        Patience : float
            The average time a customer is willing to wait in the queue. A simple 
            estimator for the patience is calculated by dividing the total waiting 
            time (including the waiting times of the abandoned customers) by the 
            number of abandonments. It is important to filter out extreme values 
            in advance. (Patience ≥ 0)
            
        Returns
        -------
        float
            The optimal number of agents such that the service-level objective is satisfied.
        """
    
        def __new__(cls,SL:float,Forecast:float,AHT:list,Awt:float,Lines:int,Patience:float):
             Parallel=int(len(AHT))
             output['Parallel']=Parallel
             output['function']='agentsServiceLevelErlangChat'
             for i in AGENTS.SLA.__new__.__annotations__:
                 output[i]=locals()[i]
             return request(output)
    class ASA():
        """
        Parameters
        ----------
        W : float
            The Average Speed of Answer (also known as average waiting time) is the time
            that an arbitrary customer with infinite patience would incur. (W > 0)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : list
            The Average Handling Time of a call. (AHT > 0). The difference between 
            this and the previous AHT parameter is that the AHT should be a range 
            of cells instead of a single number. The number of elements in the range
            determines the maximum number of concurrent chats that an agent can do. 
            This parameter is exclusively used in the Chat functions.
        Lines : int
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
            Note: setting a default of 5* your top interval arrival # is good 
            practice, but remember it’s really about the capacity your company has 
            bought from the telephony provider.
        Patience : float
            The average time a customer is willing to wait in the queue. A simple 
            estimator for the patience is calculated by dividing the total waiting 
            time (including the waiting times of the abandoned customers) by the 
            number of abandonments. It is important to filter out extreme values 
            in advance. (Patience ≥ 0)
            
        Returns
        -------
        float
            The optimal number of agents such that the W objective is satisfied.
        """
       
        def __new__(cls,W:float,Forecast:float,AHT:list,Lines:int,Patience:float):
             Parallel=int(len(AHT))
             output['Parallel']=Parallel
             output['function']='agentsWaitingTimeErlangChat'
             for i in AGENTS.ASA.__new__.__annotations__:
                 output[i]=locals()[i]
             return request(output)
         
    class ABANDON():
        """
        Parameters
        ----------
        Ab : float
            The probability that an arbitrary customer will abandon. 
            (0 < Ab < 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : list
            The Average Handling Time of a call. (AHT > 0). The difference between 
            this and the previous AHT parameter is that the AHT should be a range 
            of cells instead of a single number. The number of elements in the range
            determines the maximum number of concurrent chats that an agent can do. 
            This parameter is exclusively used in the Chat functions.
        Lines : int
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
            Note: setting a default of 5* your top interval arrival # is good 
            practice, but remember it’s really about the capacity your company has 
            bought from the telephony provider.
        Patience : float
            The average time a customer is willing to wait in the queue. A simple 
            estimator for the patience is calculated by dividing the total waiting 
            time (including the waiting times of the abandoned customers) by the 
            number of abandonments. It is important to filter out extreme values 
            in advance. (Patience ≥ 0)
            
        Returns
        -------
        float
            The optimal number of agents such that the abandonment objective is satisfied.
        """
       
        def __new__(cls,ab:float,Forecast:float,AHT:list,Lines:int,Patience:float):
             Parallel=int(len(AHT))
             output['Parallel']=Parallel
             output['function']='agentsAbandonmentsErlangChat'
             for i in AGENTS.ABANDON.__new__.__annotations__:
                 output[i]=locals()[i]
             return request(output)
         
    class OCCUPANCY():
        """
        Parameters
        ----------
        Occupancy : float
            The occupancy of the agents (0 < Occupancy ≤ 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : list
            The Average Handling Time of a call. (AHT > 0). The difference between 
            this and the previous AHT parameter is that the AHT should be a range 
            of cells instead of a single number. The number of elements in the range
            determines the maximum number of concurrent chats that an agent can do. 
            This parameter is exclusively used in the Chat functions.
        Lines : int
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
            Note: setting a default of 5* your top interval arrival # is good 
            practice, but remember it’s really about the capacity your company has 
            bought from the telephony provider.
        Patience : float
            The average time a customer is willing to wait in the queue. A simple 
            estimator for the patience is calculated by dividing the total waiting 
            time (including the waiting times of the abandoned customers) by the 
            number of abandonments. It is important to filter out extreme values 
            in advance. (Patience ≥ 0)
       
        Returns
        -------
        float
            The optimal number of agents such that the occupancy objective is satisfied.
        """
       
        def __new__(cls,Occ:float,Forecast:float,AHT:list,Lines:int,Patience:float):
             Parallel=int(len(AHT))
             output['Parallel']=Parallel
             output['function']='agentsOccupancyErlangChat'
             for i in AGENTS.OCCUPANCY.__new__.__annotations__:
                 output[i]=locals()[i]
             return request(output)
         
class ASA():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : list
        The Average Handling Time of a call. (AHT > 0). The difference between 
        this and the previous AHT parameter is that the AHT should be a range 
        of cells instead of a single number. The number of elements in the range
        determines the maximum number of concurrent chats that an agent can do. 
        This parameter is exclusively used in the Chat functions.
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : int
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
        Note: setting a default of 5* your top interval arrival # is good 
        practice, but remember it’s really about the capacity your company has 
        bought from the telephony provider.
    Patience : float
        The average time a customer is willing to wait in the queue. A simple 
        estimator for the patience is calculated by dividing the total waiting 
        time (including the waiting times of the abandoned customers) by the 
        number of abandonments. It is important to filter out extreme values 
        in advance. (Patience ≥ 0)
        
    Returns
    -------
    float
        The average speed of answer.
    """
    
    def __new__(cls,Forecast:float,AHT:list,Agents:float,Lines:int,Patience:float):
         Parallel=int(len(AHT))
         output['Parallel']=Parallel
         output['function']='waitingtimeErlangChat'
         for i in ASA.__new__.__annotations__:
             output[i]=locals()[i]
         return request(output)

class ABANDON():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : list
        The Average Handling Time of a call. (AHT > 0). The difference between 
        this and the previous AHT parameter is that the AHT should be a range 
        of cells instead of a single number. The number of elements in the range
        determines the maximum number of concurrent chats that an agent can do. 
        This parameter is exclusively used in the Chat functions.
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : int
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
        Note: setting a default of 5* your top interval arrival # is good 
        practice, but remember it’s really about the capacity your company has 
        bought from the telephony provider.
    Patience : float
        The average time a customer is willing to wait in the queue. A simple 
        estimator for the patience is calculated by dividing the total waiting 
        time (including the waiting times of the abandoned customers) by the 
        number of abandonments. It is important to filter out extreme values 
        in advance. (Patience ≥ 0)
        
    Returns
    -------
    float
        The fraction of customers that abandon chats.
    """
   
    def __new__(cls,Forecast:float,AHT:list,Agents:float,Lines:int,Patience:float):
         Parallel=int(len(AHT))
         output['Parallel']=Parallel
         output['function']='abandonmentsErlangChat'
         for i in ABANDON.__new__.__annotations__:
             output[i]=locals()[i]
         return request(output)
 
     
class OCCUPANCY():
    """
    Parameters
    ----------
    Ab : float
        The probability that an arbitrary customer will abandon. 
        (0 < Ab < 1)
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : list
        The Average Handling Time of a call. (AHT > 0). The difference between 
        this and the previous AHT parameter is that the AHT should be a range 
        of cells instead of a single number. The number of elements in the range
        determines the maximum number of concurrent chats that an agent can do. 
        This parameter is exclusively used in the Chat functions.
    Lines : int
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
        Note: setting a default of 5* your top interval arrival # is good 
        practice, but remember it’s really about the capacity your company has 
        bought from the telephony provider.
    Patience : float
        The average time a customer is willing to wait in the queue. A simple 
        estimator for the patience is calculated by dividing the total waiting 
        time (including the waiting times of the abandoned customers) by the 
        number of abandonments. It is important to filter out extreme values 
        in advance. (Patience ≥ 0)
        
    Returns
    -------
    float
        The optimal number of agents such that the abandonment objective is satisfied.
    """
   
    def __new__(cls,Forecast:float,AHT:list,Agents:float,Lines:int,Patience:float):
         Parallel=int(len(AHT))
         output['Parallel']=Parallel
         output['function']='occupancyErlangChat'
         for i in OCCUPANCY.__new__.__annotations__:
             output[i]=locals()[i]
         return request(output)

       