def rr(events, timer, waiting_processes,cpu_process,io_list,cs,t_cs):
	global all_process
	event = events[timer]
	#na: new arrival
	if 'na' in event:
		if timer == 0:
			print("time %dms: Simulator started for RR " % timer, end='')
			print_queue(waiting_processes)
			proccess = waiting_processes.pop(0)
		#Scan all processs to add in waiting list
		cs.append(proccess)
		if timer + t_cs not in events:
			events[timer + t_cs] = {}
		events[timer+t_cs]['ps'] =True



	if 'ps' in event:
		if cs and not cpu_process:
			proccess = cs.pop()
			Process.n_cs += 1
			cpu_process.append)(proccess)
            print("time %dms: P%d started using the CPU " % (timer, process.pid), end='')

