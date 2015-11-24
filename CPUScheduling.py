from collections import deque
import sys


class Process:
    algorithm = ''
    n_cs = 0

    def __init__(self, spec):
        self.pid, self.burst_t, self.n_burst, self.io_t, self.pri = spec

        self.n_burst_rmn = self.n_burst
        self.burst_t_rmn = self.burst_t
        self.curr_pri = self.pri
        self.waiting_t = 0
        self.total_waiting_t = 0
        self.queue_n = -1
        self.ent_queue_t = 0
        self.total_turnaround_t = 0

    def reset(self):
        self.n_burst_rmn = self.n_burst
        self.burst_t_rmn = self.burst_t
        self.curr_pri = self.pri
        self.waiting_t = 0
        self.total_waiting_t = 0
        self.ent_queue_t = 0
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
        elif self.algorithm == 'PWA':
            return self.curr_pri < other.curr_pri or \
                   (self.curr_pri == other.curr_pri and self.queue_n < other.queue_n)
        else:
            return self.pid < other.pid

    def __eq__(self, other):
        return self.pid == other.pid


# print the status of queue
def print_queue(q):
    rc = '[Q'
    for item in q:
        rc = rc + ' ' + str(item.pid)
    rc += ']'
    print(rc)


def srt(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs):
    event = events[timer]
    if 'ss' in event:
        print("time %dms: Simulator started for SRT " % timer, end='')
        print_queue(waiting_processes)
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
            print("time %dms: P%d started using the CPU " % (timer, process.pid), end='')
            print_queue(waiting_processes)

            if timer + process.burst_t_rmn not in events:
                events[timer + process.burst_t_rmn] = {}
            events[timer + process.burst_t_rmn]['pc'] = True

    if 'pc' in event and cpu_process and cpu_process[0].burst_t_rmn == 0:
        process = cpu_process.pop()
        process.finish(timer)
        if process.n_burst_rmn == 0:
            print("time %dms: P%d terminated " % (timer, process.pid), end='')
            print_queue(waiting_processes)
        else:
            print("time %dms: P%d completed its CPU burst " % (timer, process.pid), end='')
            print_queue(waiting_processes)
            if process.io_t == 0:
                waiting_processes.append(process)
                process.ent_queue_t = timer
                waiting_processes.sort()
            else:
                io_list.append(process)
                print("time %dms: P%d performing I/O " % (timer, process.pid), end='')
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
                    print("time %dms: P%d completed I/O " % (timer, process.pid), end='')

                    if not cpu_process and not cs:
                        print_queue(waiting_processes)
                        process2 = waiting_processes.pop(0)
                        cs.append(process2)
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
                        print("time %dms: P%d preempted by P%d " % (timer, process2.pid, process.pid), end='')
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
    f.write('-- total number of context switches: %d\n\n' % Process.n_cs)


def main():
    f = open('processes.txt', 'r')
    r = open('simout.txt', 'w')

    n = 0
    t_cs = 13

    waiting_processes = deque([])   # a queue to store waiting processes
    io_list = []                    # a list to store processes using I/O
    cpu_process = []                # a list to store process using CPU
    cs = []
    all_process = []

    for line in f:
        line = line.rstrip()
        if line == '' or line[0] == '#':
            continue
        process_spec = [int(s) for s in line.split('|')]

        if len(process_spec) != 5:
            sys.exit("Invalid input format")

        process = Process(process_spec)
        all_process.append(process)
        waiting_processes.append(process)
        n += 1

    Process.algorithm = "SRT"
    Process.n_cs = 0
    waiting_processes = []
    for process in all_process:
        process.reset()
        waiting_processes.append(process)
    waiting_processes.sort()
    print()

    timer = 0
    events = {0: {}}
    events[0]['ss'] = True
    while True:
        if timer in events:
            srt(events, timer, waiting_processes, cpu_process, io_list, cs, t_cs)
            # print(timer, events)
        if not waiting_processes and not cpu_process and not io_list and not cs:
            print("time %dms: Simulator for SRT ended " % timer, end='')
            print_queue(waiting_processes)
            break
        for p in waiting_processes:
            p.waiting_t += 1
        for p in cpu_process:
            p.burst_t_rmn -= 1
        timer += 1

    # r.write('Algorithm SRT\n')
    # analysis(all_process, r)

    f.close()


if __name__ == "__main__":
    main()
