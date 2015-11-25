"""
Team Member:
    Yunang Chen
    Ruiqi Ma

This project is written in Python 3.
"""
import sys


class Process:
    algorithm = ''
    n_cs = 0

    def __init__(self, spec):
        self.pid, self.arrival_t, self.burst_t, self.n_burst, self.io_t, self.memory = spec

        self.init_arrival_t = self.arrival_t
        self.n_burst_rmn = self.n_burst
        self.burst_t_rmn = self.burst_t
        self.waiting_t = 0
        self.total_waiting_t = 0
        self.queue_n = -1
        self.slice_rmn = 80
        self.ent_queue_t = self.arrival_t
        self.total_turnaround_t = 0

    def reset(self):
        self.arrival_t = self.init_arrival_t
        self.n_burst_rmn = self.n_burst
        self.burst_t_rmn = self.burst_t
        self.waiting_t = 0
        self.total_waiting_t = 0
        self.ent_queue_t = self.arrival_t
        self.total_turnaround_t = 0

    def compute_burst(self):
        return self.n_burst * self.burst_t

    def finish(self, timer):
        self.burst_t_rmn = self.burst_t
        self.n_burst_rmn -= 1
        self.total_waiting_t += self.waiting_t
        turnaround_t = timer - self.ent_queue_t
        self.total_turnaround_t += turnaround_t
        self.waiting_t = 0

    def __lt__(self, other):
        if self.algorithm == 'SRT':
            return self.burst_t_rmn < other.burst_t_rmn or \
                   (self.burst_t_rmn == other.burst_t_rmn and self.pid < other.pid)
        else:
            return self.pid < other.pid

    def __eq__(self, other):
        return self.pid == other.pid


class Memory:
    algorithm = ''

    def __init__(self, size):
        self.size = size
        self.map = []
        for i in range(size):
            self.map.append('.')
        self.process_list = []

    def __str__(self):
        rc = '=' * 32 + '\n'
        for i in range(self.size):
            rc += self.map[i]
            if i % 32 == 31:
                rc += '\n'
        rc += '=' * 32
        return rc

    def reset(self):
        self.map.clear()
        for i in range(self.size):
            self.map.append('.')
        self.process_list.clear()

    def next_free_partitions(self, i, p_size):
        start = end = -1
        j = i
        while end - start < p_size and j < i + self.size:
            while j != i + self.size and self.map[j % self.size] != '.':
                j += 1
            if self.map[j % self.size] == '.':
                start = j % self.size
                while j % self.size + 1 != self.size and self.map[(j + 1) % self.size] == '.':
                    j += 1
                end = j % self.size
            j += 1
        if end - start >= p_size:
            return start, end
        else:
            return -1, -1

    def place(self, p_name, p_size):
        start = end = -1
        if self.algorithm == 'First-Fit':
            start, end = self.next_free_partitions(0, p_size)
        if self.algorithm == 'Next-Fit':
            i = 0
            if self.process_list:
                i = self.process_list[-1][1] + self.process_list[-1][2]
            start, end = self.next_free_partitions(i, p_size)
        if self.algorithm == 'Best-Fit':
            free_spaces = []
            i = 0
            while i < self.size:
                start, end = self.next_free_partitions(i, p_size)
                if start != -1:
                    if free_spaces and (start, end) == free_spaces[0]:
                        break
                    free_spaces.append((start, end))
                    i = end + 1
                else:
                    break

            free_spaces.sort(key=lambda index: index[1] - index[0])
            if len(free_spaces) == 0:
                return False
            start, end = free_spaces[0]

        if start == -1:
            return False
        else:
            for i in range(p_size):
                self.map[i + start] = p_name
            self.process_list.append([p_name, start, p_size])
            return True

    def deallocate(self, p_name):
        for i in range(self.size):
            if self.map[i] == p_name:
                self.map[i] = '.'
        for i in range(len(self.process_list)):
            if self.process_list[i][0] == p_name:
                self.process_list.pop(i)
                break

    def defrag(self):
        backup = []
        for i in range(self.size):
            if self.map[i] != '.':
                backup.append(self.map[i])
        while len(backup) < self.size:
            backup.append('.')
        count = i = 0
        while backup[i] == self.map[i] and backup[i] != '.':
            i += 1
        while i < self.size:
            if backup[i] != '.':
                count += 1
            i += 1
        self.map = backup
        return count



# print the status of queue
def print_queue(q):
    rc = '[Q'
    for item in q:
        rc = rc + ' ' + str(item.pid)
    rc += ']'
    print(rc)


def srt(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs, memory, defrag_t):
    event = events[timer]
    if 'pa' in event:
        waiting_processes.sort()
        process = waiting_processes[0]
        if not cpu_process:
            process = waiting_processes.pop(0)
            cs.append(process)
            if timer + t_cs not in events:
                events[timer + t_cs] = {}
            events[timer + t_cs]['ps'] = True
        elif cpu_process and process.burst_t < cpu_process[0].burst_t_rmn:
            process = waiting_processes.pop(0)
            print_queue(waiting_processes)
            process2 = cpu_process.pop()
            waiting_processes.append(process2)
            waiting_processes.sort()
            cs.append(process)
            print("time %dms: Process '%s' preempted by Process '%s' " % (timer, process2.pid, process.pid), end='')
            print_queue(waiting_processes)
            if timer + t_cs not in events:
                events[timer + t_cs] = {}
            events[timer + t_cs]['ps'] = True


    if 'ps' in event:
        if cs and not cpu_process:
            process = cs.pop()
            Process.n_cs += 1
            cpu_process.append(process)
            print("time %dms: Process '%s' started using the CPU " % (timer, process.pid), end='')
            print_queue(waiting_processes)

    if 'pc' in event and cpu_process and cpu_process[0].burst_t_rmn == 0:
        process = cpu_process.pop()
        process.finish(timer)
        if process.n_burst_rmn == 0:
            print("time %dms: Process '%s' terminated " % (timer, process.pid), end='')
            print_queue(waiting_processes)
            memory.deallocate(process.pid)
            print("time %dms: Simulated Memory:" % timer)
            print(memory)
        else:
            print("time %dms: Process '%s' completed its CPU burst " % (timer, process.pid), end='')
            print_queue(waiting_processes)
            if process.io_t == 0:
                waiting_processes.append(process)
                process.ent_queue_t = timer
                waiting_processes.sort()
            else:
                io_list.append(process)
                print("time %dms: Process '%s' performing I/O " % (timer, process.pid), end='')
                print_queue(waiting_processes)
                if timer + process.io_t not in events:
                    events[timer + process.io_t] = {}
                    events[timer + process.io_t]['ioe'] = [process.pid]
                else:
                    events[timer + process.io_t]['ioe'].append(process.pid)
                    events[timer + process.io_t]['ioe'].sort()
        if waiting_processes:
            process2 = waiting_processes.pop(0)
            cs.append(process2)
            if timer + t_cs not in events:
                events[timer + t_cs] = {}
            events[timer + t_cs]['ps'] = True

    if 'ioe' in event:
        for pid in event['ioe']:
            for process in io_list:
                if process.pid == pid:
                    waiting_processes.append(process)
                    process.ent_queue_t = timer
                    waiting_processes.sort()
                    print("time %dms: Process '%s' completed I/O " % (timer, process.pid), end='')

                    if not cpu_process and not cs:
                        print_queue(waiting_processes)
                        process2 = waiting_processes.pop(0)
                        cs.append(process2)
                        if timer + t_cs not in events:
                            events[timer + t_cs] = {}
                        events[timer + t_cs]['ps'] = True
                    elif cpu_process and process.burst_t < cpu_process[0].burst_t_rmn and timer not in defrag_t:
                        process = waiting_processes.pop(0)
                        print_queue(waiting_processes)
                        process2 = cpu_process.pop()
                        waiting_processes.append(process2)
                        waiting_processes.sort()
                        cs.append(process)
                        print("time %dms: Process '%s' preempted by Process '%s' " % (timer, process2.pid, process.pid), end='')
                        print_queue(waiting_processes)
                        if timer + t_cs not in events:
                            events[timer + t_cs] = {}
                        events[timer + t_cs]['ps'] = True
                    else:
                        print_queue(waiting_processes)

                    io_list.remove(process)
                    break


def analysis(all_process, f):
    n_burst_tot = 0
    burst_t_tot = 0
    wait_t_tot = 0
    turnaround_t_tot = 0
    for process in all_process:
        n_burst_tot += process.n_burst
        burst_t_tot += process.compute_burst()
        wait_t_tot += process.total_waiting_t
        turnaround_t_tot += process.total_turnaround_t
    burst_t_avg = burst_t_tot / n_burst_tot
    wait_t_avg = wait_t_tot / n_burst_tot
    turnaround_t_avg = turnaround_t_tot / n_burst_tot
    f.write('-- average CPU burst time: %.2f ms\n' % burst_t_avg)
    f.write('-- average wait time: %.2f ms\n' % wait_t_avg)
    f.write('-- average turnaround time: %.2f ms\n' % turnaround_t_avg)
    f.write('-- total number of context switches: %d\n' % Process.n_cs)


def rr(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs, t_slice, memory, defrag_t):
    event = events[timer]
    if 'pa' in event:
        process = waiting_processes[0]
        if not cpu_process:
            process = waiting_processes.pop(0)
            cs.append(process)
            if timer + t_cs not in events:
                events[timer + t_cs] = {}
            events[timer + t_cs]['ps'] = True

    if 'ps' in event:
        if cs and not cpu_process:
            process = cs.pop()
            Process.n_cs += 1
            cpu_process.append(process)
            process.slice_rmn = t_slice
            print("time %dms: Process '%s' started using the CPU " % (timer, process.pid), end='')
            print_queue(waiting_processes)

    if 'slice' in event:
        if waiting_processes:
            process = cpu_process.pop()
            waiting_processes.append(process)
            print("time %dms: Process '%s' preempted due to time slice expiration" % (timer, process.pid), end='')
            print_queue(waiting_processes)
            if waiting_processes:
                process2 = waiting_processes.pop(0)
                cs.append(process2)
                if timer + t_cs not in events:
                    events[timer + t_cs] = {}
                events[timer + t_cs]['ps'] = True
        else:
            process = cpu_process[0]
            process.slice_rmn = t_slice

    if 'pc' in event and cpu_process and cpu_process[0].burst_t_rmn == 0:
        process = cpu_process.pop()
        process.finish(timer)
        if process.n_burst_rmn == 0:
            print("time %dms: Process '%s' terminated " % (timer, process.pid), end='')
            print_queue(waiting_processes)
            memory.deallocate(process.pid)
            print("time %dms: Simulated Memory:" % timer)
            print(memory)
        else:
            print("time %dms: Process '%s' completed its CPU burst " % (timer, process.pid), end='')
            print_queue(waiting_processes)
            if process.io_t == 0:
                waiting_processes.append(process)
                process.ent_queue_t = timer
            else:
                io_list.append(process)
                print("time %dms: Process '%s' performing I/O " % (timer, process.pid), end='')
                print_queue(waiting_processes)
                if timer + process.io_t not in events:
                    events[timer + process.io_t] = {}
                    events[timer + process.io_t]['ioe'] = [process.pid]
                else:
                    events[timer + process.io_t]['ioe'].append(process.pid)
                    events[timer + process.io_t]['ioe'].sort()
        if waiting_processes:
            process2 = waiting_processes.pop(0)
            cs.append(process2)
            if timer + t_cs not in events:
                events[timer + t_cs] = {}
            events[timer + t_cs]['ps'] = True

    if 'ioe' in event:
        for pid in event['ioe']:
            for process in io_list:
                if process.pid == pid:
                    waiting_processes.append(process)
                    process.ent_queue_t = timer
                    print("time %dms: Process '%s' completed I/O " % (timer, process.pid), end='')

                    if not cpu_process and not cs:
                        print_queue(waiting_processes)
                        process2 = waiting_processes.pop(0)
                        cs.append(process2)
                        if timer + t_cs not in events:
                            events[timer + t_cs] = {}
                        events[timer + t_cs]['ps'] = True

                    else:
                        print_queue(waiting_processes)

                    io_list.remove(process)
                    break


def main():
    f = open('processes.txt', 'r')
    r = open('simout.txt', 'w')

    n = 0
    t_cs = 13
    t_slice = 80
    t_memmove = 10
    placement_algorithm = ['First-Fit', 'Next-Fit', 'Best-Fit']

    waiting_processes = []   # a queue to store waiting processes
    io_list = []                    # a list to store processes using I/O
    cpu_process = []                # a list to store process using CPU
    cs = []
    all_process = []
    memory = Memory(256)
    defrag_t = []

    for line in f:
        line = line.rstrip()
        if line == '' or line[0] == '#':
            continue
        process_spec = [int(s) if s.isdigit() else s for s in line.split('|')]
        print(process_spec)
        if len(process_spec) != 6:
            sys.exit("Invalid input format")

        process = Process(process_spec)
        all_process.append(process)
        waiting_processes.append(process)
        n += 1
    latest_arrival = max([process.arrival_t for process in all_process])

    Process.algorithm = "SRT"
    Process.n_cs = 0
    events = {0: {}}

    for algo in placement_algorithm:
        Memory.algorithm = algo
        Process.n_cs = 0
        waiting_processes = []
        for process in all_process:
            process.reset()
        memory.reset()
        defrag_t = []
        tot_defrag_t = 0

        timer = 0
        events.clear()
        events = {0: {}}
        print("time %dms: Simulator started for SRT and %s" % (timer, Memory.algorithm))
        while True:
            if len(defrag_t) > 0 and timer == defrag_t[-1] + 1:
                print("time %dms: Completed defragmentation (moved %d memory units)" % (timer, len(defrag_t) / t_memmove))
                print("time %dms: Simulated Memory:" % timer)
                print(memory)
                defrag_t = []
            for p in all_process:
                if p.arrival_t == timer:
                    if timer in defrag_t:
                        p.arrival_t = defrag_t
                        continue
                    if memory.place(p.pid, p.memory):
                        waiting_processes.append(p)
                        print("time %dms: Process '%s' added to system" % (timer, p.pid), end='')
                        print_queue(waiting_processes)
                        print("time %dms: Simulated Memory:" % timer)
                        print(memory)
                        if timer not in events:
                            events[timer] = {}
                        events[timer]['pa'] = True
                    else:
                        print("time %dms: Process '%s' unable to be added; lack of memory " % (timer, p.pid))
                        print("time %dms: Starting defragmentation (suspending all processes)" % timer)
                        print("time %dms: Simulated Memory:" % timer)
                        print(memory)
                        defrag_t = range(timer, timer + t_memmove * memory.defrag())
                        tot_defrag_t += len(defrag_t)
                        p.arrival_t = defrag_t[-1] + 1
            if timer in events:
                srt(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs, memory, defrag_t)
            if not waiting_processes and not cpu_process and not io_list and not cs and timer > latest_arrival:
                print("time %dms: Simulator for SRT ended " % timer, end='')
                print_queue(waiting_processes)
                break
            for p in waiting_processes:
                p.waiting_t += 1
            for p in cpu_process:
                if timer in defrag_t:
                    p.waiting_t += 1
                else:
                    p.burst_t_rmn -= 1
                    if p.burst_t_rmn == 0:
                        if timer + 1 not in events:
                            events[timer + 1] = {}
                        events[timer + 1]['pc'] = True
            timer += 1

        print("\n\n")

        r.write('Algorithm SRT and %s\n' % Memory.algorithm)
        analysis(all_process, r)
        r.write('Defragmentation Time: %d ms (%.2f%% of total simulation time)\n\n' % (tot_defrag_t, 100 * tot_defrag_t / timer))

    Process.algorithm = 'RR'
    for algo in placement_algorithm:
        Memory.algorithm = algo
        Process.n_cs = 0
        waiting_processes = []
        for process in all_process:
            process.reset()
        memory.reset()
        defrag_t = []
        tot_defrag_t = 0

        timer = 0
        events.clear()
        events = {0: {}}
        print("time %dms: Simulator started for RR (t_slice 80) and %s" % (timer, Memory.algorithm))
        while True:
            if len(defrag_t) > 0 and timer == defrag_t[-1] + 1:
                print("time %dms: Completed defragmentation (moved %d memory units)" % (timer, len(defrag_t) / t_memmove))
                print("time %dms: Simulated Memory:" % timer)
                print(memory)
                defrag_t = []
            for p in all_process:
                if p.arrival_t == timer:
                    if timer in defrag_t:
                        p.arrival_t = defrag_t
                        continue
                    if memory.place(p.pid, p.memory):
                        waiting_processes.append(p)
                        print("time %dms: Process '%s' added to system" % (timer, p.pid), end='')
                        print_queue(waiting_processes)
                        print("time %dms: Simulated Memory:" % timer)
                        print(memory)
                        if timer not in events:
                            events[timer] = {}
                        events[timer]['pa'] = True
                    else:
                        print("time %dms: Process '%s' unable to be added; lack of memory " % (timer, p.pid))
                        print("time %dms: Starting defragmentation (suspending all processes)" % timer)
                        print("time %dms: Simulated Memory:" % timer)
                        print(memory)
                        defrag_t = range(timer, timer + t_memmove * memory.defrag())
                        tot_defrag_t += len(defrag_t)
                        p.arrival_t = defrag_t[-1] + 1
            if timer in events:
                rr(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs, t_slice, memory, defrag_t)
            if not waiting_processes and not cpu_process and not io_list and not cs and timer > latest_arrival:
                print("time %dms: Simulator for RR ended " % timer, end='')
                print_queue(waiting_processes)
                break
            for p in waiting_processes:
                p.waiting_t += 1
            for p in cpu_process:
                if timer in defrag_t:
                    p.waiting_t += 1
                else:
                    p.burst_t_rmn -= 1
                    p.slice_rmn -= 1
                    if p.burst_t_rmn == 0:
                        if timer + 1 not in events:
                            events[timer + 1] = {}
                        events[timer + 1]['pc'] = True
                    elif p.slice_rmn == 0:
                        if timer + 1 not in events:
                            events[timer + 1] = {}
                        events[timer + 1]['slice'] = True
            timer += 1

        r.write('Algorithm RR and %s\n' % Memory.algorithm)
        analysis(all_process, r)
        r.write('Defragmentation Time: %d ms (%.2f%% of total simulation time)\n\n' % (tot_defrag_t, 100 * tot_defrag_t / timer))
        print('\n\n')

    f.close()


if __name__ == "__main__":
    main()
