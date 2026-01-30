import os
import re
import configparser
from itertools import count
import random
import configparser
from pathlib import Path
import csv
import gymnasium as gym
#import gym
import numpy as np
import json
import pickle
import pathlib
import threading
import time

# pyjnius 的调用
import jnius_config
if not jnius_config.vm_running:
    jnius_config.set_classpath('/home/chaofan/Documents/pyhyflex/hhrl/hyflex/*')
from jnius import autoclass

# 输入文件路径
problemjson_path = '/home/chaofan/Documents/pyhyflex/hhrl/hyflex/problems_json/'

# 输出路径设置
_output_path_dir = "/home/chaofan/Documents/pyhyflex/hhrl/results/"

# 定义 Solution 类
class Solution:
    def __init__(self, id, solution, fitness):
        self.id = id
        self.solution = solution
        self.fitness = fitness

    def __len__(self):
        return len(self.solution)

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return (self.fitness, self.id) < (other.fitness, other.id)

    def __le__(self, other):
        return self.fitness <= other.fitness

    def __gt__(self, other):
        return (self.fitness, self.id) > (other.fitness, other.id)

    def __ge__(self, other):
        return self.fitness >= other.fitness

    def copy(self):
        return copy.deepcopy(self)

    def compare(self, other):
        return self.solution == other.solution

    def distance(self, other):
        return 0

# 定义 ListSolution 类
class ListSolution(Solution):
    def __init__(self, id=0, solution=[], fitness=float('inf')):
        super().__init__(id, solution, fitness)

    def __str__(self):
        return str(self.solution)

    def __len__(self):
        return len(self.solution)

    def distance(self, other):
        diff = [1 if a != b else 0 for a, b in zip(self.solution, other.solution)]
        diff.extend([1] * abs(len(self) - len(other)))
        return np.mean(diff)

    def generate_random(self, n=10):
        self.solution = tuple(np.random.permutation(n))

# 定义 StatsInfo 类
class StatsInfo:
    def __init__(self, initial_fitness):
        self.fitness_hist = []  # 记录每次迭代的当前适应度值
        self.best_fitness_hist = []  # 记录每次迭代的最佳适应度值
        self.heuristic_hist = []  # 记录应用的启发式方法
        self.reward_hist = []  # 记录每次迭代的奖励值
        self.best_solution = None  # 最佳解决方案
        self.run_id = 0  # 运行标识符
        self.run_time = 0.0  # 运行时间
        self.initial_fitness = initial_fitness  # 初始适应度值
        self.best_fitness = None  # 最佳适应度值
        self.iterations = 0  # 迭代次数
        self.state_hist = []  # 记录每次迭代的状态

    def __str__(self):
        return str(self.best_fitness)

    def push_heuristic(self, heuristic, reward, state=None):
        self.heuristic_hist.append(heuristic)
        self.reward_hist.append(reward)
        if state:
            self.state_hist.append(state)

    def push_fitness(self, current, best):
        self.fitness_hist.append(current)
        self.best_fitness_hist.append(best)

    def save(self, outdir='.', save_csv=False):
        filepath = f'{outdir}/{self.run_id}.dat'
        pickle.dump(self, open(filepath, 'wb'))
        if save_csv:
            self.save_csv(outdir)

    def save_csv(self, outdir='.'):
        filename = 'fitness_history'
        history = self.best_fitness_hist
        initial = self.initial_fitness
        open_flag = 'w'
        if os.path.isfile(f'{outdir}/{filename}.csv'):
            open_flag = 'a'
        with open(f'{outdir}/{filename}.csv', open_flag, newline='') as evol_file:
            w = csv.writer(evol_file, delimiter=';')
            if open_flag == 'w':
                w.writerow(('run', 'iter', 'fitness'))
                w.writerow((self.run_id, 0, initial))
            for it, fitness in enumerate(history):
                line = (self.run_id, it+1, fitness)
                w.writerow(line)

                
# 定义 AcceptAll 类
class AcceptAll:
    def is_solution_accepted(self, *args):
        return True

# 定义 RawImprovementPenalty 类
class RawImprovementPenalty:
    def __init__(self, config, actions, *args):
        pass

    def get_reward(self, action, new_fitness, past_fitness, *args):
        fir = (past_fitness - new_fitness) / past_fitness
        return fir

    def reset(self):
        pass

# 定义 StateBuilder 类
class StateBuilder:
    def __init__(self, state_classes, config, **kwargs):
        self.states = [state_cls(config, **kwargs) for state_cls in state_classes]

    def reset(self):
        for state_obj in self.states:
            state_obj.reset()

    def get_state(self):
        state = []
        for state_obj in self.states:
            state.extend(state_obj.get_state())
        return state

    def update(self, **kwargs):
        for state_obj in self.states:
            state_obj.update(**kwargs)


# 定义 FitnessImprovementRate 类
class FitnessImprovementRate:
    def __init__(self, config, **kwargs):
        self.discrete = config['FIR'].getboolean('discrete', False)
        self.fir = 0
        self.last_fitness = None

    def reset(self):
        self.fir = 0
        self.last_fitness = None

    def _get_discrete_state(self):
        if self.fir > 0:
            return 1
        elif self.fir == 0:
            return 0
        else:
            return -1

    def get_state(self):
        if self.discrete:
            return [self._get_discrete_state()]
        return [self.fir]

    def update(self, solution, **kwargs):
        if self.last_fitness is not None:
            self.fir = (self.last_fitness - solution.fitness) / self.last_fitness
        self.last_fitness = solution.fitness

# 定义 ElapsedTime 类
class ElapsedTime:
    def __init__(self, config, time_limit, **kwargs):
        self.time_limit = time_limit
        self.elapsed = 0

    def reset(self):
        pass

    def get_state(self):
        return [self.elapsed / self.time_limit]

    def update(self, elapsed, **kwargs):
        self.elapsed = elapsed

# 定义 Agent 类
class Agent:
    def __init__(self, actions, policy):
        self.actions = actions
        self.policy = policy

    def reset(self):
        raise NotImplementedError

    def select(self):
        action_idx = self.policy.select(self)
        return self.actions[action_idx]

    def get_env_state(self):
        return None

    def update(self, **kwargs):
        raise NotImplementedError

# 定义 RandomAgent 类
class RandomAgent(Agent):
    def __init__(self, config, actions, state_env, prior=[], **kwargs):
        super().__init__(actions, RoulettePolicy(config))
        self.prior = prior
        n_actions = len(actions)
        if len(prior) != n_actions:
            self.prior = [float(1/n_actions)] * n_actions
        self.value_estimates = self.prior
        self.state_env = state_env
        self.state = self.state_env.get_state()

    def __str__(self):
        return f'Random Selection'

    def reset(self):
        self.value_estimates = self.prior

    def get_env_state(self):
        return self.state

    def update(self, action, reward, solution, elapsed):
        self.state_env.update(action=action, 
                              reward=reward, 
                              solution=solution, 
                              elapsed=elapsed)
        self.state = self.state_env.get_state()

# 定义 RoulettePolicy 类
class RoulettePolicy:
    def __init__(self, config):
        pass

    def __str__(self):
        return f'Roulette Wheel'

    def select(self, agent):
        sample = range(len(agent.actions))
        return random.choices(sample, weights=agent.value_estimates)[0]
    
# 定义 HyFlexDomain 类
class HyFlexDomain:
    solution_indexer = count(1)

    def __init__(self, problem_str, instance_id, seed, problemjson_path=problemjson_path):
        with open(problemjson_path + f'{problem_str}.json', 'r') as json_file:
            self.problem_dict = json.load(json_file)
        ProblemClass = autoclass(self.problem_dict['class'])
        self.problem = ProblemClass(seed)
        self.problem.loadInstance(instance_id)
        try:
            self.instance_name = self.problem_dict['instances'][str(instance_id)]
        except KeyError:
            self.instance_name = f'id_{instance_id}'
        self.actions = self.problem_dict['actions']

    def initialise_solution(self, idx=0):
        self.problem.initialiseSolution(idx)

    def get_fitness(self, idx=0):
        return self.problem.getFunctionValue(idx)

    def apply_heuristic(self, llh, src_idx=0, dest_idx=1):
        #print(f'llh: {llh}')
        return self.problem.applyHeuristic(int(llh), int(src_idx), int(dest_idx))

    def accept_solution(self, src_idx=1, dest_idx=0):
        self.problem.copySolution(src_idx, dest_idx)

    def get_best_fitness(self):
        return self.problem.getBestSolutionValue()

    def get_solution(self, idx=0):
        solution_str = self.problem.solutionToString(idx)
        id = next(self.solution_indexer)
        return Solution(id, solution_str, self.get_fitness(idx))

# 定义 BinPacking 类
class BinPacking(HyFlexDomain):
    re_bin_items = re.compile(r'(\d+\.0, )')

    def __init__(self, instance_id, seed):
        super().__init__('BP', instance_id, seed)

    def get_solution(self, idx=0):
        solution_str = self.problem.solutionToString(idx)
        sorted_bins = []
        for bin in solution_str.split('\n')[:-2]:
            items = [float(it.strip('[, ]')) for it in re.findall(self.re_bin_items, bin)]
            sorted_bins.append(sorted(items))
        sorted_bins.sort()
        fitness = self.get_fitness(idx)
        id = next(self.solution_indexer)
        return ListSolution(id, sorted_bins, fitness)


# 定义 TSP 类
class TravelingSalesman(HyFlexDomain):
    def __init__(self, instance_id, seed):
        HyFlexDomain.__init__(self, 'TSP', instance_id, seed)

    def get_solution(self, idx=0):
        solution_str = self.problem.solutionToString(idx)
        solution_str = solution_str.split('\n')[1].strip()
        permutation = tuple((int(x) for x in solution_str.split(' ')))
        fitness = self.get_fitness(idx)
        id = next(self.solution_indexer)
        return ListSolution(id, permutation, fitness)

    
# 定义 字典 （先定义后声明）

# 定义代理对象的字典，包含了各种代理的名称和对应的类
agent_dict = {
        'RAND': RandomAgent,
        }
# 定义奖励对象的字典，包含了各种奖励的名称和对应的类
reward_dict = {
        'RIP': RawImprovementPenalty,
        }
# 定义状态对象的字典，包含了各种状态的名称和对应的类
state_dict = {
        'S7': [FitnessImprovementRate, ElapsedTime],
        }
# 定义接受对象的字典，包含了各种接受对象的名称和对应的类
acceptance_dict = {
    'ALL': AcceptAll,
        }
# 定义问题对象的字典，包含了各种问题的名称和对应的类
domain_dict = {
        'TSP': TravelingSalesman,
        'BP': BinPacking,
        }


# 最后定义

def create_env(problem, instance_id, seed, run_id, iteration_limit, config_path, save_path, overwrite):
    # 放入HyFlexEnv的定义
    class HyFlexEnv(gym.Env):
        def __init__(self, problem, instance_id, seed, run_id, 
                     iteration_limit=1000, 
                     config_path=config_path, save_path=save_path,
                     overwrite=True):
            super(HyFlexEnv, self).__init__()

            self.lock = threading.Lock()
            self.problem = problem
            self.instance_id = instance_id
            self.seed = seed
            self.config_path = config_path
            self.run_id = run_id
            self.iteration_limit = iteration_limit
            self.config_path = config_path
            self.save_path = save_path
            self.overwirte = overwrite
        
            self._setup()
        
        def _setup(self):
            # 同样的 setup 代码，但确保在每次调用 step 时进行检查
            _config_parser = configparser.ConfigParser()
            _config_parser.read(self.config_path)

            _path = pathlib.Path(_output_path_dir) / f'{self.run_id}.dat'
            if (_path / f'{self.run_id}.dat').exists() and not self.overwirte:
                return None

            self.problem_instance = domain_dict[self.problem](self.instance_id, self.seed)
            self.actions = self.problem_instance.actions
            self.state_env = StateBuilder(state_dict['S7'], 
                                 _config_parser, 
                                 actions=self.actions, 
                                 time_limit=self.iteration_limit)  
            self.agent = agent_dict['RAND'](_config_parser, self.actions, state_env=self.state_env)
            self.credit_assignment = reward_dict['RIP'](_config_parser, self.actions)
            self.acceptance = acceptance_dict['ALL']()
            self.action_space = gym.spaces.Discrete(len(self.actions))
            self.observation_space = gym.spaces.Box(low=0, 
                                                    high=1, 
                                                    shape=(len(self.state_env.get_state()),),
                                                    dtype=np.float32)
            


        def __elapsed_time(self):
            self.elapsed = time.process_time() - self.start_time
            return self.elapsed    

        def reset(self, seed=None, options=None):
            self.problem_instance.initialise_solution()
            self.current_fitness = self.problem_instance.get_fitness()
            self.stats = StatsInfo(self.current_fitness)
            self.stats.push_fitness(self.current_fitness, self.current_fitness)
            self.start_time = time.process_time()
            self.iteration = 0
            self.done = False
            self.elapsed = 0
            ob = np.array(self.state_env.get_state(), dtype=np.float32)
            info = {}
            return ob, info
        
        def step(self, action):

            #with self.lock:

            #llh = self.agent.select()
            if action < 0 or action >= self.action_space.n:
                raise ValueError(f"Action {action} is out of range for the action space.")

            fitness = self.problem_instance.apply_heuristic(action)
            delta = self.current_fitness - fitness
            reward = self.credit_assignment.get_reward(action, fitness, self.current_fitness)
            if self.acceptance.is_solution_accepted(delta):
                self.problem_instance.accept_solution()
                self.current_fitness = fitness
            self.agent.update(action=action, reward=reward,
                              solution=self.problem_instance.get_solution(), 
                              elapsed=self.elapsed)
            self.stats.push_fitness(self.current_fitness, self.problem_instance.get_best_fitness())
            self.stats.push_heuristic(action, reward, self.agent.get_env_state())
            self.iteration += 1

            #if self.iteration % 100 == 0:
                #print(f'self.iteration: {self.iteration}')

            if self.iteration >= self.iteration_limit:
                self.done = True
                self.stats.best_fitness = self.problem_instance.get_best_fitness()
                self.stats.run_time = self.elapsed
                self.stats.iterations = self.iteration

            ob = np.array(self.state_env.get_state(), dtype=np.float32)
            
            terminated = self.done
            truncated = False
            info = {}

            return ob, reward, terminated, truncated, info
        
        
        def __save_results(self):
            _path = Path(self.save_path) / f'{self.run_id}.dat'
            _path.mkdir(parents=True, exist_ok=True)
            self.stats.save(_path, save_csv=True)
            
        def render(self, mode='human'):
            # 实现render方法
            pass

        def close(self):
            # 实现close方法
            pass
             
    return HyFlexEnv(problem, instance_id, seed, run_id, iteration_limit, config_path, save_path, overwrite)


