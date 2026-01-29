
from ERLANG.settings import output
from ERLANG.settings import request

# =============================================================================
# ERLANG X FUNCTIONS
# Depending on their values, either the Erlang C, Erlang X, or a combination of 
# the two models is used in the following functions. Note that some parameters in
# the Erlang X functions are optional, these parameters are filled in with default
# values. If an optional parameter is used, all other optional parameters 
# must also be filled in.
# =============================================================================

class SLA:  
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
    Definition : int
        A flag to switch between different modes of calculating the service level. 
        0 = virtual service level; 1 = answered; 2 = offered (default).
    Variance : float
        The variance of the forecast. All models take fluctuations in the number of 
        arrivals into account. This is characterized by the Poisson distribution, 
        for which the variance is equal to the expectation. The Variance parameter 
        can be used in case the variance is bigger than the expectation. 
        (Variance ≥ Forecast)
    
    Returns
    -------
    float
        The expected service level.
    """
    
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Awt:float,Lines:int=None,Patience:float=None,Retrials:float=None,Definition:int=None,Variance:float=None):
        if Lines!=None and Patience!=None and Retrials!=None and Variance!=None and Definition!=None:
            output['function']='serviceLevelErlangXDV'
        elif Lines!=None and Patience!=None and Retrials!=None and Definition==None and Variance!=None:
            output['function']='serviceLevelErlangXV'
        elif Lines!=None and Patience!=None and Retrials!=None and Definition!=None and Variance==None:
            output['function']='serviceLevelErlangXD'
        elif Lines!=None and Patience!=None and Definition==None and Variance==None:
            output['function']='serviceLevelErlangX'
        elif (Lines!=None and Patience==None and Retrials==None and Definition==None and Variance==None):
            output['function']='serviceLevelErlangCL'
        elif Lines==None and Patience==None and Retrials==None and Definition==None and Variance==None:
            output['function']='serviceLevelErlangC'      
        else:
            output['function']=None   
        for i in SLA.__new__.__annotations__:
            output[i]=locals()[i]
            if Retrials==None:
                output['Retrials'] = 0
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
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
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
        Retrials : float
            The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
        Definition : int
            A flag to switch between different modes of calculating the service level. 
            0 = virtual service level; 1 = answered; 2 = offered (default).
        Variance : float
            The variance of the forecast. All models take fluctuations in the number of 
            arrivals into account. This is characterized by the Poisson distribution, 
            for which the variance is equal to the expectation. The Variance parameter 
            can be used in case the variance is bigger than the expectation. 
            (Variance ≥ Forecast)
        
        Returns
        -------
        float
            The optimal number of agents such that the service-level objective is satisfied.
        """
        
        def __new__(cls,SL:float,Forecast:float,AHT:float,Awt:float,Lines:int=None,Patience:float=None,Retrials:float=None,Definition:int=None,Variance:float=None):
            if Lines!=None and Patience!=None and Retrials!=None and Variance!=None and Definition!=None:
                output['function']='agentsServiceLevelErlangXDV'
            elif Lines!=None and Patience!=None and Retrials!=None and Definition==None and Variance!=None:
                output['function']='agentsServiceLevelErlangXV'
            elif Lines!=None and Patience!=None and Retrials!=None and Definition!=None and Variance==None:
                output['function']='agentsServiceLevelErlangXD'
            elif Lines!=None and Patience!=None and Definition==None and Variance==None:
                output['function']='agentsServiceLevelErlangX'
            elif (Lines!=None and Patience==None and Retrials==None and Definition==None and Variance==None):
                output['function']='agentsServiceLevelErlangCL'
            elif Lines==None and Patience==None and Retrials==None and Variance==None  and Definition==None:
                output['function']='agentsServiceLevelErlangC'
            else:
                output['function']=None    
            for i in AGENTS.SLA.__new__.__annotations__:
                output[i]=locals()[i]
                if Retrials == None:
                    output['Retrials'] = 0
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
        AHT:AHT : list
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
            The average speed of answer.
        """

        def __new__(cls,W:float,Forecast:float,AHT:float,Lines:int=None,Patience:float=None,Retrials:float=None):
            if Lines!=None and Patience!=None:
                output['function']='agentsWaitingTimeErlangX'
            elif Lines!=None and Patience==None and Retrials==None:
                output['function']='agentsWaitingTimeErlangCL'
            elif Lines==None and Patience==None and Retrials==None:
                output['function']='agentsWaitingTimeErlangC'
            else:
                output['function']=None    
            for i in AGENTS.ASA.__new__.__annotations__:
                output[i]=locals()[i]
                if Retrials == None:
                    output['Retrials'] = 0
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
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
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
        Retrials : float
            The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
            
        Returns
        -------
        float
            The optimal number of agents such that the abandonment objective is satisfied.
        """

        def __new__(cls,ab:float,Forecast:float,AHT:float,Lines:int,Patience:float,Retrials:float):      
            output['function']='agentsAbandonmentErlangX'
            for i in AGENTS.ABANDON.__new__.__annotations__:
                output[i]=locals()[i]
            return request(output)
    
    class BLOCKING():
        """
        Parameters
        ----------
        B : float
            The expected blocking probability. (0 < B < 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
        
        Returns
        -------
        float
            The optimal number of agents such that the blocking objective is satisfied.
        """
       
        def __new__(cls,B:float,Forecast:float,AHT:float):
            output['function']='agentsBlockingErlangB'
            for i in AGENTS.BLOCKING.__new__.__annotations__:
                output[i]=locals()[i]
            return request(output)
    
    class MONTHLY():
        """
        Parameters
        ----------
        SL : float
            The expected Service Level of an arbitrary non-blocked customer. (0 < SL < 1)
        Forecast : float
            The average number of arrivals per month
        AHT : float
            The Average Handling Time of a call in seconds. (AHT > 0). The difference between 
            this and the previous AHT parameter is that the AHT should be a range 
            of cells instead of a single number. The number of elements in the range
            determines the maximum number of concurrent chats that an agent can do. 
            This parameter is exclusively used in the Chat functions.
        Awt : float
            The Acceptable Waiting Time is the maximum allowed waiting time.
            Customers that wait shorter than the Awt have received, per definition,
            a good service. The service level is defined as the percentage of 
            customers that are served within the Awt. The time unit is the same as 
            the others and, hence, is not necessarily in seconds! (Awt ≥ 0)
        Available_seconds_per_period : float
            The amount of seconds which exist in the current working period. (> 0)
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
        Retrials : 
        
        Returns
        -------
        float
            The expected service level.
        """
        
        def __new__(cls, SL: float, Volume: float, AHT_seconds: float, Available_seconds_per_period: float, AWT_seconds: float):

            forecast_per_minute = Volume / (Available_seconds_per_period / 60)

            aht_minutes = AHT_seconds / 60
            awt_minutes = AWT_seconds / 60

            # put all converted values as parameters.
            output['function'] = 'agentsServiceLevelErlangC'

            output['SL'] = SL
            output['Forecast'] = forecast_per_minute
            output['AHT'] = aht_minutes
            output['Awt'] = awt_minutes
            

            print("🔍 Request being sent:", output)
            return request(output)
    
    
    class OCCUPANCY():
        """
        Parameters
        ----------
        Occupancy : float
            The occupancy of the agents (0 < Occupancy ≤ 1)
        Forecast : float
            The average number of arrivals per unit of time. (Forecast ≥ 0)
        AHT : float
            The Average Handling Time of a call. (AHT > 0)
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
        Retrials : float
            The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)      

        Returns
        -------
        float
            The optimal number of agents such that the occupancy objective is satisfied.
        """
       
        def __new__(cls,Occ:float,Forecast:float,AHT:float,Lines:int=None,Patience:float=None,Retrials:float=None):
            if Lines!=None and Patience!=None:
                output['function'] = 'agentsOccupancyErlangX'
            elif Lines!=None and Patience==None and Retrials==None:
                output['function'] = 'agentsOccupancyErlangCL'
            elif Lines==None and Patience==None and Retrials==None:
                output['function'] = 'agentsOccupancyErlangC'
            else:
                output['function'] = None
            for i in AGENTS.OCCUPANCY.__new__.__annotations__:
                output[i]=locals()[i]
                if Retrials == None:
                    output['Retrials'] = 0
            return request(output)
        
    
class FORECAST():
    """
    Parameters
    ----------
    SL : float
        The expected Service Level of an arbitrary non-blocked customer. (0 < SL < 1)
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
    Definition : int
        A flag to switch between different modes of calculating the service level. 
        0 = virtual service level; 1 = answered; 2 = offered (default).
    
    Returns
    -------
    float
        The maximum average number of arrivals per unit of time such that the 
        service-level objective is satisfied.
    """
    
    def __new__(cls,SL:float,AHT:float,Agents:float,Awt:float,Lines:int=None,Patience:float=None,Retrials:float=None,Definition:int=None):
        if Lines!=None and Patience!=None and Retrials!=None and Definition!=None:
            output['function']='forecastServiceLevelErlangXD'
        elif Lines!=None and Patience!=None and Definition==None:
            output['function']='forecastServiceLevelErlangX'
        elif (Lines!=None and Patience==None and Retrials==None and Definition==None):
            output['function']='forecastServiceLevelErlangCL'
        elif Lines==None and Patience==None and Retrials==None and Definition==None:
            output['function']='forecastServiceLevelErlangC'
        else:
            output['function']=None    
        for i in FORECAST.__new__.__annotations__:
            output[i]=locals()[i]
            if Retrials==None:
                output['Retrials'] = 0
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
    
    Returns
    -------
    float
        The average speed of answer.
    """

    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines:int=None,Patience:float=None,Retrials:float=None):
        if Lines!=None and Patience!=None:
            output['function']='waitingtimeErlangX'
        elif Lines!=None and Patience==None and Retrials==None:
            output['function']='waitingtimeErlangCL'
        elif Lines==None and Patience==None and Retrials==None:
            output['function']='waitingtimeErlangC'
        else:
            output['function']=None    
        for i in ASA.__new__.__annotations__:
            output[i]=locals()[i]
            if Retrials==None:
                output['Retrials'] = 0
        return request(output)

class ABANDON():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)
    Variance : float
        The variance of the forecast. All models take fluctuations in the number of 
        arrivals into account. This is characterized by the Poisson distribution, 
        for which the variance is equal to the expectation. The Variance parameter 
        can be used in case the variance is bigger than the expectation. 
        (Variance ≥ Forecast)
    
    Returns
    -------
    float
        The fraction of customers that abandon.
    """

    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines:int,Patience:float,Retrials:float,Variance:float=None):
        if Variance!=None:
            output['function']='abandonmentsErlangXV'
        elif Variance==None:
            output['function']='abandonmentsErlangX'
        else:
            output['function']=None
        for i in ABANDON.__new__.__annotations__:
            output[i]=locals()[i]
        return request(output)



class RETRIALRATE():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)      

    Returns
    -------
    float
        The average number of customers that retrial per unit of time.
    """

    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines:int,Patience:float,Retrials:float):              
        output['function']='retrialrateErlangX'
        for i in RETRIALRATE.__new__.__annotations__:
            output[i]=locals()[i]
        return request(output)

class BLOCKING():
    """
    Parameters
    ----------
    Forecast : float
        The average number of arrivals per unit of time. (Forecast ≥ 0)
    AHT : float
        The Average Handling Time of a call. (AHT > 0)
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)      

    Returns
    -------
    float
        The fraction of customers that are blocked.
    """
   
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines:int,Patience:float,Retrials:float):             
        if Retrials!=None:
            output['function']='blockingprobErlangX'
        for i in BLOCKING.__new__.__annotations__:
            output[i]=locals()[i]
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
    Retrials : float
        The probability that a customer who abandons, redials. (0 ≤ Retrials ≤ 1)      

    Returns
    -------
    float
        The occupancy of the agents.
    """
   
    def __new__(cls,Forecast:float,AHT:float,Agents:float,Lines:int=None,Patience:float=None,Retrials:float=None):             
        if Lines!=None and Patience!=None:
            output['function']='occupancyErlangX'
        elif Lines!=None and Patience==None and Retrials==None:
            output['function']='occupancyErlangCL'
        elif Lines==None and Patience==None and Retrials==None:
            output['function']='occupancyErlangC'
        else:
            output['function']=None
        for i in OCCUPANCY.__new__.__annotations__:
            output[i]=locals()[i]
            if Retrials==None:
                output['Retrials'] = 0
        return request(output)

