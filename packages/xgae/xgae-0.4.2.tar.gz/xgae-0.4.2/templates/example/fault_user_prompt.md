# Objective
 - Strictly follow the task steps in TODO.MD to process user instructions. 
 - Do not execute any steps not listed. 
 - Terminate the process immediately if any task fails without retrying.
 
# TODO.MD
     Process Title: Alarm and Fault Query Process
     Process Summary: Achieve precise fault location through resource alarm detection and classification
    Task[1]: Fault Object Processing
    Step[1]: Query alarm records of target resource
    Step[2]: Check for uncleared alarms
    Step[3]: If no alarms exist, terminate process and return normal status
    Step[4]: If alarms exist, proceed to alarm type analysis
    Step[5]: Determine if alarm type is business layer (type=1)
    Step[6]: If yes, trigger business fault location module
    Step[7]: Else determine if alarm type is device layer (type=2)
    Step[8]: If yes, trigger device fault location module
    Step[9]: Else determine if alarm type is middleware (type=3)
    Step[10]: If yes, trigger middleware fault location module
    Task[2]: Solution Retrieval
    Step[1]: For business alarms, call get_busi_fault_cause to query business fault solutions
    Step[2]: For device alarms, call query_equip_fault_cause to query device fault solutions
    Step[3]: For middleware alarms, call web_search to query middleware fault solutions