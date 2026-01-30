 
from matplotlib import pyplot as plt
import seaborn as sns

plt.style.use(['science', 'ieee', 'no-latex'])
colors = ['black','red','blue','green','brown','orange','violet','pink','light blue','teal','yellow','magenta','dark green','dark red','dark orange']
palette = sns.xkcd_palette(colors)
sns.set_palette(palette)
plt.rcParams['font.family'] =['Times New Roman','SimSun']
plt.rcParams['font.size'] = 10.5
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.rm'] = 'Times New Roman'
plt.rcParams['mathtext.it'] = 'Times New Roman:italic'