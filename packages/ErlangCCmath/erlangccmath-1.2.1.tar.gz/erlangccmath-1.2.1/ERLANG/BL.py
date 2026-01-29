from ERLANG.settings import output
from ERLANG.settings import request

# =============================================================================
# ERLANG BLENDING FUNCTIONS
# In the blending model, agents will work on inbound as well as outbound calls. 
# If an agent becomes available, they will prioritize inbound calls and will 
# only take on outbound calls when other agents are left idle.
# =============================================================================
    
class SLA():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Awt : float
        The Acceptable Waiting Time is the maximum allowed waiting time.
        Customers that wait shorter than the Awt have received, per definition,
        a good service. The service level is defined as the percentage of 
        customers that are served within the Awt. The time unit is the same as 
        the others and, hence, is not necessarily in seconds! (Awt ≥ 0)
    Lines : Integer 
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. Every customer occupies 1 line. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
    patience : float
        The average time a customer is willing to wait in the queue. 
    Threshold : float
        The number of agents that are kept idle before taking outbound calls into 
        service. (Threshold ≤ Agents)
        
    Returns
    -------
    float
        The expected service level.
    """
   
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Awt:float, Lines: float, Patience: float,Threshold:float):
        output['function']='serviceLevelBlending'
        for i in SLA.__new__.__annotations__:
            output[i]=locals()[i]
            print("🔍 Request being sent:", output)
        return request(output)

class ASA():
     
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : Integer 
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
    patience : float
        The average time a customer is willing to wait in the queue. 
    Threshold : float
        The number of agents that are kept idle before taking outbound calls into 
        service. This way, threshold amount of people are always ready for incomming calls. (Threshold ≤ Agents)
    
    Returns
    -------
    float
        The average speed of answer.
    """
   
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines: int, Patience: float,Threshold:float):
        output['function']='waitingtimeBlending'
        for i in ASA.__new__.__annotations__:
            output[i]=locals()[i]
            print("🔍 Request being sent:", output)
        return request(output)
    


class OCCUPANCY():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : Integer 
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
    patience : float
        The average time a customer is willing to wait in the queue. 
    Threshold : float
        The number of agents that are kept idle before taking outbound calls into 
        service. (Threshold ≤ Agents)
    
    Returns
    -------
    float
        The occupancy of the agents.
    """

    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines: int, Patience: float,Threshold:float):
        output['function']='occupancyBlending'
        for i in OCCUPANCY.__new__.__annotations__:
            output[i]=locals()[i]
            print("🔍 Request being sent:", output)
        return request(output)
    
    
class OUTBOUND():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : Integer 
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
    patience : float
        The average time a customer is willing to wait in the queue. 
    Threshold : float
        The number of agents that are kept idle before taking outbound calls into 
        service. (Threshold ≤ Agents)
    
    Returns
    -------
    float
        The average number of outbound calls per unit of time.
    """
    
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines: int, Patience: float,Threshold:float, OutboundAHT: float):
        output['function']='outboundBlending'
        for i in OUTBOUND.__new__.__annotations__:
            output[i]=locals()[i]
            print("🔍 Request being sent:", output)
        return request(output)
    
class Abandonments():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
    Agents : float
        Represents the number of agents; it can be real. (Agents ≥ 0)
    Lines : Integer 
        The Lines parameter is the limit on the total number of customers that 
        can be in the system at the same time, consisting of: lines in use by 
        customers in service, and lines in use by customers that wait. A new 
        arriving customer will be blocked if all lines are occupied. 
        (Lines ≥ Agents, integer). 
    patience : float
        The average time a customer is willing to wait in the queue. 
    Threshold : float
        The number of agents that are kept idle before taking outbound calls into 
        service. (Threshold ≤ Agents)
    
    Returns
    -------
    float
        The average number of outbound calls per unit of time.
    """
    
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines: int, Patience: float,Threshold:float):
        output['function']='abandonmentsBlending'
        for i in Abandonments.__new__.__annotations__:
            output[i]=locals()[i]
            print("🔍 Request being sent:", output)
        return request(output)
        
class THRESHOLD():


    class SLA():
        """
        Parameters
        ----------
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Agents : float
            The number of agents handling calls; may be fractional for calculation purposes. (Agents ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue. 
        SL : float
            Target Service Level (fraction of calls answered within Awt) for dimensioning.  
            Must satisfy 0 < SL < 1.
        Awt : float
            Acceptable Waiting Time: the threshold within which a call is still counted as “on-time”.  
            Service Level is defined as the fraction of calls answered within this time. (Awt ≥ 0)

            
        Returns
        -------
        float
            The average number of outbound calls per unit of time based on the 
            service-level objective.
        """
       
        def __new__(cls,Forecast:float,AHT:float,Agents: float,Lines: int,Patience: float,SL:float,Awt : float):
            output['function']='thresholdServiceLevelBlending'
            for i in THRESHOLD.SLA.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)
        

    class ASA():
        """
        Parameters
        ----------
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Agents : float
            The number of agents handling calls; may be fractional for calculation purposes. (Agents ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue. 
        W : float
            Target average Speed of Answer (ASA) in same time-unit as AHT and Awt. (W ≥ 0)

            
        Returns
        -------
        float
            the threshold based on ASA
        """
        def __new__(cls, Forecast:float,AHT:float,Agents: float, Lines: int, Patience: float, W : float):
            output['function']='thresholdWaitingTimeBlending'
            for i in THRESHOLD.ASA.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)
        
    class Abandonments():
        """
        Parameters
        ----------
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Agents : float
            The number of agents handling calls; may be fractional for calculation purposes. (Agents ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        ab : float
            Target abandonment rate (fraction of calls that abandon). (0 ≤ ab < 1)

            
        Returns
        -------
        float
            the threshold based on ASA
        """
        def __new__(cls, Forecast:float,AHT:float,Agents: float,Lines: int,Patience: float, ab: float):
            output['function']='thresholdAbandonmentBlending'
            for i in THRESHOLD.Abandonments.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)
        
    class Occupancy():
        """
        Parameters
        ----------
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Agents : float
            The number of agents handling calls; may be fractional for calculation purposes. (Agents ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Occ : float
            Target occupancy level (fraction of time agents are busy). (0 ≤ Occ < 1)

            
        Returns
        -------
        float
            the threshold based on ASA
        """
        def __new__(cls, Forecast:float,AHT:float,Agents: float,Lines: int, Patience: float, Occ: float):
            output['function']='thresholdOccupancyBlending'
            for i in THRESHOLD.Occupancy.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)
        
    class Outbound():
        """
        Parameters
        ----------
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Agents : float
            The number of agents handling calls; may be fractional for calculation purposes. (Agents ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Outbound : float
            The average number of outbound arrivals per unit of time  
        OutboundAHT : float
            Average Handling Time of an outbound call.  

            
        Returns
        -------
        float
            the threshold based on ASA
        """
        def __new__(cls, Forecast:float,AHT:float,Agents: float, Lines: int, Patience: float, Outbound: float, OutboundAHT: float):
            output['function']='thresholdOutboundBlending'
            for i in THRESHOLD.Outbound.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)

class AGENTS():
    
    
    class SLA():
        """
        Parameters
        ----------
        SL : float
            The expected Service Level of an arbitrary non-blocked customer. (0 < SL < 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Awt : float
            The Acceptable Waiting Time is the maximum allowed waiting time.
            Customers that wait shorter than the Awt have received, per definition,
            a good service. The service level is defined as the percentage of 
            customers that are served within the Awt. The time unit is the same as 
            the others and, hence, is not necessarily in seconds! (Awt ≥ 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Blending Outound : float
            The average number of outbound arrivals per unit of time 
        Blending Outboud AHT : float
            The average handling time of the outbound emails

            
        Returns
        -------
        float
            The average number of outbound calls per unit of time based on the 
            service-level objective.
        """
       
        def __new__(cls,SL:float, Forecast:float,AHT:float,Awt:float, Lines: int, Patience: float, Outbound:float, OutboundAHT:float):
            output['function']='agentsServiceLevelBlending'
            for i in AGENTS.SLA.__new__.__annotations__:
                output[i]=locals()[i]
            print("🔍 Request being sent:", output)
            return request(output)
        
    class ASA():
        """
        Parameters
        ----------
        ASA : float
            Desired average speed of answer
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Blending Outound : float
            The average number of outbound arrivals per unit of time
        Blending Outboud AHT : float
            The average handling time of the outbound emails

            
        Returns
        -------
        float
            The average number of outbound calls per unit of time based on the 
            service-level objective.
        """

        def __new__(cls,W:float,Forecast:float,AHT:float,Lines:int,Patience:float,Outbound:float, OutboundAHT:float):
            output['function']='agentsWaitingTimeBlending'
            for i in AGENTS.ASA.__new__.__annotations__:
                output[i]=locals()[i]
                print("🔍 Request being sent:", output)
            return request(output)
        
    class Abandonments():
        """
        Parameters
        ----------
        Abandonments: When not picked up before AWT, a certain percentage abandons the call since they have no more patience.
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Blending Outound : float
            The average number of outbound arrivals per unit of time
        Blending Outboud AHT : float
            The average handling time of the outbound emails

            
        Returns
        -------
        float
            The number of agents required to fulfill the abandonments case
        """

        def __new__(cls,ab:float,Forecast:float,AHT:float,Lines:int,Patience:float,Outbound:float, OutboundAHT:float):
            output['function']='agentsAbandonmentsBlending'
            for i in AGENTS.Abandonments.__new__.__annotations__:
                output[i]=locals()[i]
                print("🔍 Request being sent:", output)
            return request(output)
        
    class Occupancy():
        """
        Parameters
        ----------
        Occupancy: float
            the occupancy parameter defines the fraction of time which the agent has to be working at least.
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        Lines : Integer 
            The Lines parameter is the limit on the total number of customers that 
            can be in the system at the same time, consisting of: lines in use by 
            customers in service, and lines in use by customers that wait. A new 
            arriving customer will be blocked if all lines are occupied. 
            (Lines ≥ Agents, integer). 
        patience : float
            The average time a customer is willing to wait in the queue.
        Blending Outound : float
            The average number of outbound arrivals per unit of time
        Blending Outboud AHT : float
            The average handling time of the outbound emails

            
        Returns
        -------
        float
            The number of agents required to fulfill the occupancy case
        """

        def __new__(cls,Occ:float,Forecast:float,AHT:float,Lines:int,Patience:float,Outbound:float, OutboundAHT:float):
            output['function']='agentsOccupancyBlending'
            for i in AGENTS.Occupancy.__new__.__annotations__:
                output[i]=locals()[i]
                print("🔍 Request being sent:", output)
            return request(output)
    