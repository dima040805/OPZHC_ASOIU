import collections
import queue
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

Event = collections.namedtuple('Event', 'time proc_id action')

def compute_duration(action):
    if action == 'посадил пассажира':
        return random.expovariate(1/5)
    elif action == 'высадил пассажира':
        return random.expovariate(1/20)
    else:
        return 0

def taxi_process(ident, trips, start_time=0):
    stats = {
        'trips_completed': 0,
        'total_ride_time': 0.0,
        'total_search_time': 0.0
    }
    
    time = yield Event(start_time, ident, 'выехал из гаража')
    
    for i in range(trips):
        search_start = time
        time = yield Event(time, ident, 'посадил пассажира')
        stats['total_search_time'] += time - search_start
        
        ride_start = time
        time = yield Event(time, ident, 'высадил пассажира')
        stats['total_ride_time'] += time - ride_start
        stats['trips_completed'] += 1
    
    yield Event(time, ident, 'уехал в гараж')
    
    print(f"\n{'='*50}")
    print(f"Такси {ident}: завершение")
    print(f"  Поездок:           {stats['trips_completed']}")
    print(f"  Время в поездках:  {stats['total_ride_time']:.2f} мин")
    print(f"  Время поиска:      {stats['total_search_time']:.2f} мин")
    print(f"{'='*50}\n")

class Simulator:
    def __init__(self, procs_map):
        self.events = queue.PriorityQueue()
        self.procs = dict(procs_map)
        self.event_log = []

    def run(self, end_time):
        for _, proc in sorted(self.procs.items()):
            first_event = next(proc)
            self.events.put(first_event)
            self.event_log.append(first_event)

        sim_time = 0
        while sim_time < end_time:
            if self.events.empty():
                print('*** События закончились ***')
                break

            current_event = self.events.get()
            sim_time, proc_id, action = current_event
            self.event_log.append(current_event)
            print(f'{sim_time:6.2f} | Такси {proc_id}: {action}')

            active_proc = self.procs[proc_id]
            
            if action in ['посадил пассажира', 'выехал из гаража']:
                next_time = sim_time + compute_duration(action)
            else:
                next_time = sim_time + compute_duration(action)

            try:
                next_event = active_proc.send(next_time)
                self.events.put(next_event)
            except StopIteration:
                del self.procs[proc_id]
        else:
            if not self.events.empty():
                print(f'\n*** Время вышло: {self.events.qsize()} событий осталось ***\n')

DEPARTURE_INTERVAL = 5

def run_simulation(taxis_dict, end_time=180, title=""):
    print(f"\n{title}\n")
    for proc_id, proc in taxis_dict.items():
        print(f"Создано такси {proc_id}")
    sim = Simulator(taxis_dict)
    sim.run(end_time)
    return sim.event_log

print("="*60)
print("Задание 2: три варианта параметров (i от 3 до 9)")
print("="*60)

# Вариант 1: исходная модель (случайное количество поездок 9-15)
taxis_v1 = {}
for i in range(3, 10):
    trips = random.randint(9, 15)
    start_time = i * DEPARTURE_INTERVAL
    taxis_v1[i] = taxi_process(i, trips, start_time)

# Вариант 2: trips = (i+1)*3, start_time = i * DEPARTURE_INTERVAL (строго по методичке)
taxis_v2 = {}
for i in range(3, 10):
    trips = (i + 1) * 3
    start_time = i * DEPARTURE_INTERVAL
    taxis_v2[i] = taxi_process(i, trips, start_time)

# Вариант 3: trips = (i+1)*3, start_time = i * 3 (меньший интервал для сравнения)
taxis_v3 = {}
for i in range(3, 10):
    trips = (i + 1) * 3
    start_time = i * 3
    taxis_v3[i] = taxi_process(i, trips, start_time)

log_v1 = run_simulation(taxis_v1, 180, "Вариант 1: trips = random(9,15), start_time = i*5")
log_v2 = run_simulation(taxis_v2, 180, "Вариант 2: trips = (i+1)*3, start_time = i*5")
log_v3 = run_simulation(taxis_v3, 180, "Вариант 3: trips = (i+1)*3, start_time = i*3")

def plot_taxi_rides(event_log, title):
    taxi_data = {}
    
    for event in event_log:
        time, proc_id, action = event
        if proc_id not in taxi_data:
            taxi_data[proc_id] = {'start': [], 'end': [], 'other': []}
        
        if action == 'посадил пассажира':
            taxi_data[proc_id]['start'].append(time)
        elif action == 'высадил пассажира':
            taxi_data[proc_id]['end'].append(time)
        else:
            taxi_data[proc_id]['other'].append(time)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    colors = plt.cm.tab10.colors
    
    for proc_id, data in taxi_data.items():
        color = colors[proc_id % len(colors)]
        
        ax.scatter(data['start'], [proc_id] * len(data['start']), 
                   marker='^', color='green', s=100, zorder=3, alpha=0.8)
        ax.scatter(data['end'], [proc_id] * len(data['end']), 
                   marker='v', color='red', s=100, zorder=3, alpha=0.8)
        ax.scatter(data['other'], [proc_id] * len(data['other']), 
                   marker='o', color='blue', s=80, zorder=2, alpha=0.6)
        
        for start, end in zip(data['start'], data['end']):
            ax.plot([start, end], [proc_id, proc_id], 'k-', alpha=0.3, linewidth=1)
    
    ax.set_xlabel('Время (мин)')
    ax.set_ylabel('Номер такси')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    max_time = max([e.time for e in event_log]) + 10 if event_log else 100
    ax.set_xlim(0, max_time)
    ax.set_ylim(2.5, 9.5)
    
    start_patch = mpatches.Patch(color='green', label='Начало поездки (посадка)')
    end_patch = mpatches.Patch(color='red', label='Конец поездки (высадка)')
    other_patch = mpatches.Patch(color='blue', label='Выезд/возврат')
    ax.legend(handles=[start_patch, end_patch, other_patch], loc='upper right')
    
    plt.tight_layout()
    plt.savefig(f"{title}.png")

plot_taxi_rides(log_v1, "Вариант 1: random trips, интервал 5 мин")
plot_taxi_rides(log_v2, "Вариант 2: trips=(i+1)*3, интервал 5 мин")
plot_taxi_rides(log_v3, "Вариант 3: trips=(i+1)*3, интервал 3 мин")

def analyze_logs(logs, names):
    results = {}
    for log, name in zip(logs, names):
        taxi_stats = {}
        for event in log:
            if event.action in ['посадил пассажира', 'высадил пассажира']:
                if event.proc_id not in taxi_stats:
                    taxi_stats[event.proc_id] = {'rides': 0, 'last_start': None}
                if event.action == 'посадил пассажира':
                    taxi_stats[event.proc_id]['last_start'] = event.time
                elif event.action == 'высадил пассажира' and taxi_stats[event.proc_id]['last_start'] is not None:
                    taxi_stats[event.proc_id]['rides'] += 1
        
        total_rides = sum(stats['rides'] for stats in taxi_stats.values())
        avg_rides = total_rides / len(taxi_stats) if taxi_stats else 0
        last_time = max(e.time for e in log) if log else 0
        
        results[name] = {
            'total_rides': total_rides,
            'avg_rides': avg_rides,
            'last_time': last_time
        }
    
    print(f"\n{'Вариант':<45} {'Всего поездок':<15} {'Ср. поездок/такси':<20} {'Последнее событие':<15}")
    print("-" * 95)
    for name, stats in results.items():
        print(f"{name:<45} {stats['total_rides']:<15} {stats['avg_rides']:<20.2f} {stats['last_time']:<15.2f}")

analyze_logs(
    [log_v1, log_v2, log_v3],
    ["Вариант 1 (random 9-15, интервал 5)", "Вариант 2 ((i+1)*3, интервал 5)", "Вариант 3 ((i+1)*3, интервал 3)"]
)
