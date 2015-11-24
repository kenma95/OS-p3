#Ruiqi Ma
#Yunang Chen
#2015/11/22
#Project 3
#Please run in Python 2.7.x environment



from collections import deque
import copy
##############
#GENERIC METHOD
##############
class Proccess:
   def __init__(self,proc):
      self.proc_num = int (proc[0])
      self.arrival_time = int(proc[1])
      self.burst_time = int (proc[2])
      self.burst_time_remain= int (proc[2])
      self.num_burst = int(proc[3])
      self.io_time = int(proc[4])
      self.wait = 0
      self.memory = int(proc[5])
      self.in_mem = 0

class Io:
    def __init__(self,index,time):
        self.index = index
        self.time = time

#format print the burst queue list
def print_queue(queue,proc_list):
    printout="[Q"
    for index in queue:
        printout+= " " + str(proc_list[index].proc_num)
    printout+="]"
    return printout


##############################
#SRT
##############################
def get_next_interest_srt(burst_time_remain,switching,current_time):
    global io_list,time,proc_list_SRT
    t_time = 999
    for item in proc_list_SRT:
        if item.arrival_time > time:
            t_time = min(item.arrival_time - time,t_time)
    if current_burst != -1:
        t_time = min(burst_time_remain, t_time)
    elif switching == 0 and  not q_burst:#all burst queue finished
        t_time= min(io_list[0].time, t_time)
    elif switching == 0:
        t_time=min(burst_time_remain,t_time)
    else:
        t_time=min( switching,t_time)
    for item in io_list:
        if item.time < t_time:
            t_time = item.time
    
    return t_time

def time_pass_srt(t_time):
    global time, burst_time_remain, proc_list_SRT,current_burst,\
    q_burst,io_list,switching,t_cs,\
    stat_burst_time,stat_cs,stat_turnaround,stat_waittime
    
    add_proc=0
    skip_io_flag=0
    time+=t_time
    #turnaround stat
    if current_burst != -1:
        stat_turnaround += t_time
    stat_turnaround += len(q_burst) * t_time
    #system check
    for item in proc_list_SRT:
        if item.arrival_time == time:
            q_burst.append(item)
    q_burst.sort(key = lambda a:proc_list_SRT[a].burst_time_remain)

    if (switching!=0):  #in context switch
        switching-=t_time
        if (switching == 0):    #ready for switch
            if (q_burst):
                stat_waittime += (len(q_burst)-1)*t_cs
                stat_cs+=1
                #add new process
                current_burst = q_burst.pop(0)
                burst_time_remain=proc_list_SRT[current_burst].burst_time_remain
                print "time "+ str(time) + "ms: P"+str(proc_list_SRT[current_burst].proc_num) +" started using the CPU "+print_queue(q_burst,proc_list_SRT)
                add_proc =1

    if (burst_time_remain != 0 and add_proc==0):
        stat_waittime += len(q_burst)*t_time
        burst_time_remain =int( burst_time_remain) - t_time
        proc_list_SRT[current_burst].burst_time_remain -=t_time
        stat_burst_time+=t_time
        if burst_time_remain == 0:        #burst finished
            proc_list_SRT[current_burst].num_burst-=1
            #move to io list if have IO process
            if proc_list_SRT[current_burst].io_time != 0 and proc_list_SRT[current_burst].num_burst > 0:
                io_item = Io(current_burst,proc_list_SRT[current_burst].io_time)
                io_list.append(io_item)
                skip_io_flag=1
                print "time "+ str(time) + "ms: P"+str(proc_list_SRT[current_burst].proc_num)+" completed its CPU burst "+print_queue(q_burst,proc_list_SRT)
                #start the ioa
                print "time "+ str(time) + "ms: P"+str(proc_list_SRT[current_burst].proc_num) + " performing I/O "+print_queue(q_burst,proc_list_SRT)

            #no IO process
            #move to the end of the queue if still have num burst
            elif proc_list_SRT[current_burst].num_burst > 1:
                q_burst.append(current_burst)
                print "time "+ str(time) + "ms: P"+"completed its CPU burst "+print_queue(q_burst,proc_list_SRT)
            #terminate if neither have io time nor burst trail
            else:
                print "time "+ str(time) + "ms: P"+str(proc_list_SRT[current_burst].proc_num) + " terminated "+print_queue(q_burst,proc_list_SRT)
            if q_burst:
                switching = t_cs #reques a new context switch
            if q_burst and q_burst[0]==current_burst:
                switching = 0
            current_burst = -1

    #IO procedure
    i=0
    while i < len(io_list):
        if skip_io_flag == 0 or io_list[i]!=io_list[-1]:
            io_list[i].time-=(t_time)
        #io finished
        if io_list[i].time == 0:
            index= io_list[i].index 
            if proc_list_SRT[index].num_burst == 0:
                #process terminate
                print "time "+ str(time) + "ms: P"+str(proc_list_SRT[index].proc_num) + " terminated "+print_queue(q_burst,proc_list_SRT)
            
            else:   #process add back to q_burst
                #refill burst time
                proc_list_SRT[index].burst_time_remain = proc_list_SRT[index].burst_time
                #check preempted
                preempt = 0
                if proc_list_SRT[index].burst_time_remain < proc_list_SRT[current_burst].burst_time_remain:
                    print "time "+ str(time) + "ms: P"+str(proc_list_SRT[index].proc_num)+" completed I/O "+print_queue(q_burst,proc_list_SRT)
                    q_burst.append(index)
                    q_burst.append(current_burst)
                    q_burst.sort(key = lambda a: (proc_list_SRT[a].prior, proc_list_SRT[a].proc_num) )
                    print "time "+ str(time) + "ms: P"+str(proc_list_SRT[current_burst].proc_num) + " preempted by P" + str(proc_list_SRT[index].proc_num) + " " + print_queue(q_burst[1:],proc_list_SRT)
                    current_burst = -1
                    burst_time_remain = 0
                else:       #not preempted
                    q_burst.append(index)
                    q_burst.sort(key = lambda a: (proc_list_SRT[a].prior, proc_list_SRT[a].proc_num) )
                    print "time "+ str(time) + "ms: P"+str(proc_list_SRT[index].proc_num)+" completed I/O "+print_queue(q_burst,proc_list_SRT)                    
                switching = t_cs
            io_list.pop(i)
            i-=1
        i+=1





#####################################
#main
#####################################
if __name__ == "__main__":
    #read file
    f = open("processes.txt", "r")
    total_burst_num = 0
    proc_list_SRT = []
    for line in f:
        if line.startswith('#'):
            continue
        else:
            proc = Proccess(line.split('|'))
            total_burst_num += proc.num_burst
            proc_list_SRT.append(proc)
    #finished file read
    f.close()
    #copy list for SRT & PWA
    proc_list_RR = copy.deepcopy(proc_list_SRT)
    #finish read file manipulate
    #------------------------------


    #--------------------------------
    #SRT
    stat_burst_time = 0 #reset stat
    stat_cs = 0
    stat_turnaround = 0
    stat_waittime = 0

    time = 0    #reset time counter and queue
    t_cs =13
    switching = t_cs
    q_burst =[]
    io_list=[]
    burst_time_remain=0
    current_burst=-1

    #memory list 
    m_map = '.'*256;

    #initialize burst queue
    #start sim
    print "time "+str(time)+"ms: Simulator started for SRT " +print_queue(q_burst,proc_list_SRT)
    for item in range(0, len(proc_list_SRT)):
        if item.arrival_time == 0:
            q_burst.append(item)
    q_burst.sort(key = lambda a:proc_list_SRT[a].burst_time_remain)

    while q_burst or io_list or current_burst != -1:
        t=get_next_interest_srt(burst_time_remain,switching);
        time_pass_srt(t);
    #end sim
    print "time "+str(time)+"ms: Simulator for SRT ended " + print_queue(q_burst,proc_list_SRT) +"\n\n"
    #write to text
    f_out.write("Algorithm SRT\n")
    f_out.write("-- average CPU burst time: " + str("{0:.2f}".format(stat_burst_time/float(total_burst_num))) + " ms\n")
    f_out.write("-- average wait time: " + str("{0:.2f}".format(stat_waittime/float(total_burst_num))) + " ms\n")
    f_out.write("-- average turnaround time: " + str("{0:.2f}".format(stat_turnaround/float(total_burst_num))) + " ms\n")
    f_out.write("-- total number of context switches: " + str(stat_cs) + "\n")


    #------------------------------------------------------
    #RR
    time = 0    #reset time counter and queue
    t_cs = 13
    switching = t_cs
    t_slice = 80


  
    f_out.close()


#add_memory is called the first time a process enter the ready queue
#p: Process object that enter the queue
#algor: Placement Algorithm
#           - 0 for first fit, 1 for next-fit, 2 for best fit
# previous: previous add_memory end location, only used in algor=1
#return: return the 'previous' add_memory end location prepare for the next process added
#           -1 for fail to add, need to defrag
def add_memory(p, memory_map,algor,previous = 0):
    global m_map
    start_loc = -1
    end_loc =-1
    if algor == 0:    #first fit
        i = 0
        while i<256:
            if i == '.' and start_loc == -1:   #locate start
                start_loc = i
            if start_loc != -1 and i != '.':  #locate end
                end_loc = i 
                if end_loc - start_loc >= p.memory:     #long enough to hold
                    add_memory_exec(start_loc, p)
                    return start_loc + p.memory 
                else:   #not long enough
                    start_loc = -1
                    end_loc = -1

            i+=1
        if start_loc != -1 and end_loc == -1:
            end_loc =256
        if end_loc - start_loc >= p.memory:     #long enough to hold
            add_memory_exec(start_loc,p)
            return start_loc + p.memory 

    if algor == 1:  #next fit
        i = previous
        while i<256:
            if i == '.' and start_loc == -1:   #locate start
                start_loc = i
            if start_loc != -1 and i != '.':  #locate end
                end_loc = i
                if end_loc - start_loc >= p.memory:     #long enough to hold
                    add_memory_exec(start_loc, p)
                    return start_loc + p.memory
                else:   #not long enough
                    start_loc = -1
                    end_loc = -1
        if start_loc != -1 and end_loc == -1:
            end_loc =256
        if end_loc - start_loc >= p.memory:     #long enough to hold
            add_memory_exec(start_loc,p)
            return start_loc + p.memory
        #start from head
        i =0
        while i<previous:
            if i == '.' and start_loc == -1:   #locate start
                start_loc = i
            if start_loc != -1 and i != '.':  #locate end
                end_loc = i
                if end_loc - start_loc >= p.memory:     #long enough to hold
                    add_memory_exec(start_loc,p)
                    return start_loc + p.memory
                else:   #not long enough
                    start_loc = -1
                    end_loc = -1

    if algor ==2:  #best fit
        start_l =[]
        end_l = []
        i = 0
        while i<256:
            if i == '.' and start_loc == -1:   #locate start
                start_loc = i
            if start_loc != -1 and i != '.':  #locate end
                end_loc = i 
                if end_loc - start_loc >= p.memory:     #long enough to hold
                    start_l.append(start_loc)
                    end_l.append(end_loc)
                else:   #not long enough
                    start_loc = -1
                    end_loc = -1

            i+=1
        if start_loc != -1 and end_loc == -1:
            end_loc =256
        if end_loc - start_loc >= p.memory:     #long enough to hold
            start_l.append(start_loc)
            end_l.append(end_loc)

        if len(start_l)>0:
            suitable = 0
            for i in range(0,len(start_l)):
                if end_l[i]-start_l[i] < end_l[suitable]-start_l[suitable]:
                    suitable = i
            add_memory_exec(start_l[suitable],p)
            return start_l[suitable]+p.memory

    #not yet return, meaning no enough space
    return -1  #return -1 for defrag signal

#sub function of add_memory
def add_memory_exec(start_loc, p):
    global m_map
    for i in range(start_loc,start_loc+p.memory):
        m_map[i] = p.proc_num


#call when a process is terminated, clean the memeory
def remove_memory(p):
    global m_map
    for i in range(0,256):
        if m_map[i] == p.proc_num:
            m_map[i] = '.'



#defragmentation function
#return the cost of defrag
def defrag():
    global m_map
    back_up=[]
    for i in range(0,256):
        if m_map[i]!= '.':
            back_up.append(m_map[i])
    while len(back_up)!=256:
        back_up.append('.')
    count =0
    for i in range(0,256):
        if back_up[i]!= '.' and back_up[i]!=m_map[i]:
            count += 1
    m_map = back_up
    return count
