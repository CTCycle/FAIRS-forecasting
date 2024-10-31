import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from FAIRS.commons.utils.process.mapping import RouletteMapper
from FAIRS.commons.constants import CONFIG, STATES, NUMBERS
from FAIRS.commons.logger import logger



    
# [ROULETTE RL ENVIRONMENT]
###############################################################################
class RouletteEnvironment(gym.Env):

    def __init__(self, data : np.array, configuration):
        super(RouletteEnvironment, self).__init__()       

        self.timeseries = data[:, 0]
        self.positions = data[:, 1]
        self.colors = data[:, 2]

        mapper = RouletteMapper()          
        self.perceptive_size = configuration["dataset"]["PERCEPTIVE_SIZE"]
        
        self.initial_capital = configuration["environment"]["INITIAL_CAPITAL"]
        self.bet_amount = configuration["environment"]["BET_AMOUNT"]
        self.max_steps = configuration["environment"]["MAX_STEPS"] 
        
        self.numbers = list(range(NUMBERS)) 
        self.red_numbers = mapper.color_map['red']
        self.black_numbers = mapper.color_map['black']
        
        # Actions: 0 (Red), 1 (Black), 2-37 for betting on a specific number
        self.action_space = spaces.Discrete(STATES)
        # Observation space is the last WINDOW_SIZE numbers that appeared on the wheel
        self.observation_space = spaces.Box(low=0, high=36, shape=(self.perceptive_size,), dtype=np.int32)
        
        # Initialize state, capital, steps, and reward  
        self.extraction_index = 0 
        self.state = np.full(shape=self.perceptive_size, fill_value=-1)                       
        self.capital = self.initial_capital
        self.steps = 0
        self.reward = 0
        self.done = False
    
    # Reset the state of the environment to an initial state
    #--------------------------------------------------------------------------
    def reset(self):        
        self.extraction_index = 0
        self.state = np.full(shape=self.perceptive_size, fill_value=-1, dtype=np.int32)                  
        self.capital = self.initial_capital
        self.steps = 0
        self.done = False

        return self.state

    # Perform the action (0: Bet on Red, 1: Bet on Black, 2: Bet on Specific Number)
    #--------------------------------------------------------------------------
    def step(self, action):
        
        next_extraction = np.int32(self.timeseries[self.extraction_index])        
        self.state = np.delete(self.state, 0)
        self.state = np.append(self.state, next_extraction)
        self.extraction_index += 1

        # Calculate reward based on the action
        if 0 <= action <= 36:  # Bet on Specific Number            
            if action == next_extraction:
                self.reward = 35 * self.bet_amount 
                self.capital += 35 * self.bet_amount
            else:
                self.reward = -self.bet_amount  
                self.capital -= self.bet_amount 

        elif action == 37:  # Bet on Red
            if next_extraction in self.red_numbers:
                self.reward = self.bet_amount  
                self.capital += self.bet_amount
            else:
                self.reward = -self.bet_amount  
                self.capital -= self.bet_amount 

        elif action == 38:  # Bet on Black
            if next_extraction in self.black_numbers:
                self.reward = self.bet_amount 
                self.capital += self.bet_amount
            else:
                self.reward = -self.bet_amount  
                self.capital -= self.bet_amount         

        self.steps += 1

        # Check if the episode should end
        if self.capital <= 0 or self.steps >= self.max_steps:
            self.done = True
        else:
            self.done = False

        return self.state, self.reward, self.done, {"capital": self.capital}
    

    # Render the environment to the screen 
    #--------------------------------------------------------------------------
    def render(self, path):

        # Roulette layout: assigning colors to each number
        colors = ['green'] + ['red', 'black'] * 18
        colors = colors[:NUMBERS]  # Ensure the list has the correct length
        labels = list(range(NUMBERS))

        # Set up plot
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
        theta = np.linspace(0, 2 * np.pi, NUMBERS, endpoint=False)
        width = 2 * np.pi / NUMBERS

        # Create bars
        bars = ax.bar(theta, np.ones(NUMBERS), width=width, color=colors, edgecolor='white', align='edge')

        # Highlight the last extracted number
        extracted_number = 0 if np.all(self.state == -1) else self.state[-1]
        bars[extracted_number].set_facecolor('yellow')  # Highlight the extracted number
        bars[extracted_number].set_alpha(0.7)           # Increase opacity for emphasis

        # Adjust the position of the labels to be on the outer edge
        for i, (label, angle) in enumerate(zip(labels, theta)):
            angle_label = angle + width / 2
            x = angle_label
            y = 1.05  # Position radius just outside the wheel
            angle_deg = np.degrees(angle_label)
            if angle_deg >= 270:
                angle_deg -= 360  # Normalize angle between -90 and 270 degrees
            # Text rotation
            rotation = angle_deg
            ax.text(x, y, str(label),
                    rotation=rotation, rotation_mode='anchor',
                    ha='center', va='center', color='black', fontsize=8,
                    clip_on=False)

        # Remove the grid and axis labels
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])

        # Set the radius limit to include the labels
        ax.set_ylim(0, 1.15)

        # Add title and display current capital and reward below the wheel
        plt.title("Roulette Wheel - Current Spin")
        plt.figtext(0.5, 0.05, f"Current capital: {self.capital} | Reward: {self.reward}",
                    ha="center", fontsize=12)
        plt.figtext(0.5, 0.01, f"Last extracted number: {extracted_number}",
                    ha="center", fontsize=10)

        # Remove tight_layout since it may cause clipping in polar plots
        # plt.tight_layout()

        fig_path = os.path.join(path, 'environment_rendering.jpeg')
        plt.savefig(fig_path, bbox_inches='tight', format='jpeg', dpi=300)
        plt.close()