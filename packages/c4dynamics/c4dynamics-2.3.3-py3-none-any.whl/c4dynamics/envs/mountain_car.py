import numpy as np
import sys 
sys.path.append('.')
import c4dynamics as c4d 
# import warnings 
# from typing import Optional
from scipy import integrate, optimize


class mountain_car(c4d.state):
  '''
  A mountain car environment for a reinforcement learning problem. 


  Parameters
  ==========

  mass : float
      ...
  gravity : float
      ...
  action : float
      ...
  dt : float 
      ... 
  velocity_lim : tuple 
      ... 
  \\ position lim cannot be set becuase it determines the shape of the problem in the cos() 

  See Also 
  ========
  ... 




  **Dynamics**
  

  The state variables of a mountain car are: 

  .. math::

    X = [x, v]^T 

  Where: 
  - :math:`x` is the position of the car along the x-axis.
  - :math:`v` is the velocity of the car along the x-axis. 

  The car is goverened by the following equations of motion which represent the dynamics 
  of climbing a steep hill in the presence of gravity and resistance forces:

  .. math:: 
    \\dot{x} = v 

    \\dot{v} = g \\cdot cos(3 \\cdot x) + a_c / m - k \\cdot v / m
   
  Where:
  - :math:`x` is the position coordinate in :math:`x` direction. Default units :math:`[m]`
  - :math:`v` is the velocity coordinate in :math:`x` direction. Default units :math:`[m/s]`
  - :math:`g` is the gravity force. Defaults :math:`9.8 [N]`
  - :math:`m` is the car mass. Defaults :math:`1500 [kg]`
  - :math:`a_c` is the action (force) command. Defaults :math:`-20[N]` (left), :math:`0` (do nothing), or :math:`20[N]` (right)
  - :math:`k` is the resistance coefficient. Defaults :math:`0.5 [1/s]` 


  The position and velocity are subject to the boundaries:

  .. math:: 

    x \\in speed_lim

    v \\in [vmin, vmax]

  Where: 
  - :math:`xmin` is the minimum position coordinate in :math:`x` direction. Defaults :math:`-120 [m]`
  - :math:`xmax` is the maximum position coordinate in :math:`x` direction. Defaults :math:`50 [m]`
  - :math:`vmin` is the minimum velocity coordinate in :math:`x` direction. Default units :math:`-30 [m/s]`
  - :math:`vmax` is the maximum velocity coordinate in :math:`x` direction. Default units :math:`30 [m/s]`
  
  Outside a boundary the vairable is clipped (extraploated with last value). 


  **Reward** 
  
  
  \\ Goal: When the car reaches :math:`xmax`, the environment provides 


  **Discretization**
  ...


  Example
  =======
  ...


  '''


  def __init__(self, mode = 'physical', n_bins = 12): 
    """ 
      Args
      ---- 
        mass: mass of the car (default 0.2) 
        friction: friction in Newton (default 0.3)
        dt: time step in seconds (default 0.1)
    """
    
    self.mode = mode 
    self.n_bins = n_bins 
    
    if self.mode == 'physical': # physical scene

      self.dt = 0.1
      self.gravity = 9.8 

      self.x_lim = (-150, 50) # m
      steep_angle = 65 * c4d.d2r  # degrees to radians 

      self.mass = 1500 # kg

      self.friction = 0

      self.speed_lim = (-45, 45)  # 50m/s = 180km/h 
      self.action_list = (-4000, 0, 4000)

      self.normalized = False # True

      # h(x) = a ⋅ sin(c ⋅ x)
      self.steep_factor = 2 * np.pi / (self.x_lim[1] - self.x_lim[0])   # c 
      self.amplitude = np.tan(steep_angle) / self.steep_factor          # a
    

    elif self.mode == 'sarsa':
    
      self.dt = 0.05
      self.gravity = 9.8 
      
      self.mass = 0.1
      self.steep_factor = 3
      self.amplitude = 1
      
      self.friction = 0 # 0.1 
      self.x_lim = (-1.5, 0.5) 
      
      self.speed_lim = (-.5, .5)  
      self.action_list = (-0.5, 0, 0.5) 
      
      self.normalized = True
        
    elif self.mode == 'gymnasium':

      self.dt = 1
      self.gravity = 0.0025 

      self.mass = 1
      self.steep_factor = 3
      self.amplitude = 1
      
      self.friction = 0
      self.x_lim = (-1.2, 0.5) 
      
      self.speed_lim = (-0.07, 0.07) 
      self.action_list = (-0.001, 0, 0.001)
      
      self.normalized = True


    super().__init__(position = 0, velocity = 0) 

    xmax = self.x_lim[1] 
    vmax = self.speed_lim[1] 
    # self.e_max = self.mass * self.gravity * (np.sin((xmax - (0.5 * np.pi)) + 0.5) + 1.0) + 0.5 * vmax**2
    self.e_max = self.mass * self.gravity * self.hx(xmax) + 0.5 * self.mass * vmax**2
    
    self.state_lim = (-1, 1)
    self.state_interval = np.linspace(self.state_lim[0],    self.state_lim[1],    num = self.n_bins - 1, endpoint = False)
    

    gamma = 3.0

    uniform_interval = np.linspace(-1, 1, num = self.n_bins)
    gamma_interval = np.sign(uniform_interval) * (np.abs(uniform_interval)**gamma)      # flatten center

    self.x_interval = self.x_lim[0] + (gamma_interval + 1) * 0.5 * (self.x_lim[1] - self.x_lim[0])
    self.vel_interval = self.speed_lim[0] + (gamma_interval + 1) * 0.5 * (self.speed_lim[1] - self.speed_lim[0])

    xp = []
    for x in np.linspace(self.x_lim[0], self.x_lim[1], 5000):
      xp.append([x, integrate.quad(lambda xx: np.sqrt(1 + self.dhdx(xx)**2), self.x_lim[0], x)[0]])
    self.xp = np.array(xp)

    self.reset(exploring_starts = False)


  def hx(self, x = None): 
    '''
    takes x in earth frame and returns height on the hill. 
    h(x) = a ⋅ sin(c ⋅ x)
    dh/dx = a ⋅ c ⋅ cos(c ⋅ x) \\ = tan(θ) 
    θ = arctan(dh/dx) 
    '''
    if x is None:
      x = self.p2x(self.position)
    
    return self.amplitude * np.sin(self.steep_factor * x) 
  

  def dhdx(self, x = None): 
    '''
    h(x) = a ⋅ sin(c ⋅ x)
    dh/dx = a ⋅ c ⋅ cos(c ⋅ x) \\ = tan(θ) 
    \\ θ = arctan(dh/dx) 
    '''    
    if x is None:
      x = self.p2x(self.position)
    
    return self.amplitude * self.steep_factor * np.cos(self.steep_factor * x) 
    

  def x2p(self, x):
    """
    Arc length along hill from x0 to x
      x   |   position
    ------|------
    -150  |   0
     -50  | 108.85
      50  | 217.7
    """
    # dhdx = lambda xx: self.steep_factor * np.cos(self.steep_factor * xx)
    # position, _ = integrate.quad(lambda xx: np.sqrt(1 + self.dhdx(xx)**2), self.x_lim[0], x)
    return np.interp(x, self.xp[:, 0], self.xp[:, 1])


  def p2x(self, position):
    """
    Invert arc length to find x coordinate
    s (position) |   x 
    -------------|---------
      0          | -150
     108.85      |  -50
     217.7       |   50
    """
    # Solve s_of_x(x) = s
    
    # position = position if isinstance(position, (list, np.ndarray)) else [position]

    # func = lambda xx: self.x2p(xx) - s

    # for s in position: 

    #   s_min = self.x2p(self.x_lim[0])
    #   s_max = self.x2p(self.x_lim[1])

    #   # Clamp s to valid range
    #   if s < s_min:
    #     return self.x_lim[0]
    #   if s > s_max:
    #     return self.x_lim[1]
      
    
    # x = optimize.brentq(func, self.x_lim[0], self.x_lim[1])
    return np.interp(position, self.xp[:, 1], self.xp[:, 0])


  def step(self, action):
    """
      Performs one step in the environment following the action.
      
      Args 
      ----
        action: an integer representing one of three actions [0, 1, 2]
                where 0=move_left, 1=do_not_move, 2=move_right
      
      Returns
      -------
        (postion_t1, velocity_t1): state in the t-n frame. 
        reward: always negative but when the goal is reached
        done: True when the goal is reached
    
      Integration
      -----------
        Semi-implicit Euler integraton of the equations of motion.
        The frame of reference is the path-tangent frame. 
    """

    # x = self.p2x(self.position)
    # dh_dx = self.steep_factor * np.cos(self.steep_factor * x)
    theta = np.arctan(self.dhdx())
    
    
    # Semi-implicit Euler integraton

    # this in earth. seems wrong.
    # acc = self.action_list[action] * np.cos(theta) / self.mass               \
    #           - self.gravity * np.cos(theta) * np.sin(theta)                  \
    #             - self.friction * self.velocity / self.mass
    # something here is inconsistent. 
    # the integration is along x earth. and so are the car coordinates. 
    # but the limits refer to the body frame. for example, v=0.5 means total velocity of v=0.5 
    # and when here the velocity is allowed up to 0.5 is only in x earth, namely the total is even higher. 
    # 
    # in t-n: 
    acc = self.action_list[action] / self.mass               \
              - self.gravity * np.sin(theta)                  \
                - self.friction * self.velocity / self.mass


    self.velocity += acc * self.dt
    self.velocity = np.clip(self.velocity, *self.speed_lim)

    self.position += self.velocity * self.dt


    # self.position = np.clip(self.position, *self.x_lim[0])

    # if self.position <= self.x_lim[0] and self.velocity < 0:
    #   self.velocity = 0
    # 5. Map back to Earth to check boundaries

    # why s-n:
    # -------- 
    # engine constraints are along the path.
    # 
    # why x-y: 
    # --------
    # the hill geometry is defined in x-y.
    # easier to define boundaries.
    # nice to visualize.
    # easier to debug. intuitive. 
    #  

    x_new = self.p2x(self.position)
    reward, done = -.01, False
    
    if x_new <= self.x_lim[0]:
      self.position = self.x2p(self.x_lim[0])
      self.velocity = max(0, self.velocity) 
      
    elif x_new >= self.x_lim[1]:
      self.position = self.x2p(self.x_lim[1])
      self.velocity = min(0, self.velocity)
      reward, done = (1, True)

    self.store()
    # reward, done = (-0.01, False) if self.position < self.x_lim[1] else (1, True)
  
    return reward, done


  def energy_normalized(self, state = None):

    if state is None: 
      state = self.X

    # e_state = self.mass * self.gravity * (np.sin((state[0] - (0.5 * np.pi)) + 0.5) + 1.0) + 0.5 * state[1]**2
    e_state = self.mass * self.gravity * self.hx(self.p2x(state[0])) + 0.5 * self.mass * state[1]**2

    return e_state / self.e_max    
  

  def energy(self, state = None):

    if state is None: 
      state = self.X

    # potential energy (height modeled by sine curve)
    potential = self.mass * self.gravity * (np.sin((x - (0.5 * np.pi)) + 0.5) + 1.0)
    # kinetic energy
    kinetic = 0.5 * self.mass * v**2

    e_state = self.mass * self.gravity * (np.sin((state[0] - (0.5 * np.pi)) + 0.5) + 1.0) + 0.5 * state[1]**2
    return 2 * e_state / self.e_max    
    

  def reset(self, exploring_starts = True): 
    """ 
      Resets the car to an initial position [-1.2, 0.5]
      
      Args
      ---- 
        exploring_starts: if True a random position is taken
        initial_position: the initial position of the car (requires exploring_starts=False)
      
      Returns
      ------- 
        Initial position of the car and the velocity
    
    """

    # seed_seq = np.random.SeedSequence(seed)
    # np_seed = seed_seq.entropy
    # rng = RandomNumberGenerator(np.random.PCG64(seed_seq))
    # seed = np.random.randint(0, 2**24)
    # np.random.seed(seed)
    super().reset() 
    
    if exploring_starts: # gym: always generates. but on small interval (-0.6,-0.4 uniformly) 
      
      # initial_position = np.random.uniform(-1.2, 0.5)
      # initial_position = np.random.uniform(initial_position - 0.1, initial_position + 0.1)
      pos0 = self.x_lim[0] + (self.x_lim[1] - self.x_lim[0]) / 2
      dpos = 0.0555 * (self.x_lim[1] - self.x_lim[0]) 
      x0 = np.random.uniform(pos0 - dpos, pos0 + dpos)
    
    else:
      x0 = self.x_lim[0] + (self.x_lim[1] - self.x_lim[0]) / 2

    x0 = np.clip(x0, self.x_lim[0], self.x_lim[1])



    self.position = self.x2p(self.x_lim[0])
    self.velocity = self.speed_lim[1]
    
    # self.store()
      

  def discretize(self): 

    xi = self.p2x(self.position) # NOTE it can be left in p to save time but change intervals as well

    # if self.normalized:
    #   # normalized the state to (-1, 1) and discretize for N bins. 
    #   x_ind = np.digitize(np.interp(xi, self.x_lim, self.state_lim), self.state_interval)
    #   vel_ind = np.digitize(np.interp(self.velocity, self.speed_lim, self.state_lim), self.state_interval)
 
    # else: 
    #   # normalized the state to (-1, 1) and discretize for N bins. 
    #   x_ind = np.digitize(xi, self.x_interval)
    #   vel_ind = np.digitize(self.velocity, self.vel_interval)

    x_ind = np.argmin(np.abs(self.x_interval - xi))
    vel_ind = np.argmin(np.abs(self.vel_interval - self.velocity))


    if False: 
      import matplotlib.pyplot as plt 
      plt.switch_backend('qtagg') 
      plt.plot(self.x_interval, np.ones_like(self.x_interval), 'o'); 
      plt.plot(xi, 1, 'rx', markersize = 12);
      plt.title(f'{x_ind} / {self.n_bins}');
      plt.show(block = True)

      plt.plot(self.vel_interval, np.ones_like(self.vel_interval), 'o'); 
      plt.plot(self.velocity, 1, 'rx', markersize = 12);
      plt.title(f'{vel_ind} / {self.n_bins}');
      plt.show(block = True)

    return vel_ind.item() - 1, x_ind.item() - 1



  def render(self, file_path = './simulation_render.gif', mode = 'gif'):
    # def render(self, file_path = './mountain_car.mp4', mode = 'mp4'):
    """ 
      When the method is called it saves an animation
      of what happened until that point in the episode.
      Ideally it should be called at the end of the episode,
      and every k episodes.
      
      ATTENTION: requires avconv and/or imagemagick installed.
      
      Args
      ----
        file_path: the name and path of the video file
        mode: the file can be saved as 'gif' or 'mp4'
    
    """

    # Plot init
    fig = plt.figure()
    ax = fig.add_subplot(111, autoscale_on = False, xlim = (-1.2, 0.5), ylim = (-1.1, 1.1))
    ax.grid(False)  # disable the grid
    x_sin = np.linspace(start = -1.2, stop = 0.5, num = 100)
    y_sin = np.sin(3 * x_sin)

    # plt.plot(x, y)
    ax.plot(x_sin, y_sin)  # plot the sine wave
    # line, _ = ax.plot(x, y, 'o-', lw=2)
    dot, = ax.plot([], [], 'ro')
    time_text = ax.text(0.05, 0.9, '', transform = ax.transAxes)
    _position_list = self.data('position')[1]
    _dt = self.dt

    def _init():
      dot.set_data([], [])
      time_text.set_text('')
      return dot, time_text

    def _animate(i):
      x = _position_list[i]
      y = np.sin(3 * x)
      dot.set_data([x], [y])
      time_text.set_text("Time: " + str(np.round(i * _dt, 1)) + "s" + '\n' + "Frame: " + str(i))
      return dot, time_text


    # Argument	             | Meaning
    # --------               | -------
    # fig	                   | The figure object where the animation will be drawn.
    # _animate	             | The function that updates the animation frame by frame.
    # np.arange(1,           | The sequence of frame numbers (i) that _animate(i) will receive. 
    #   len(self.data('t'))) |	  Starts from 1 to len(self.data('t')) - 1.
    # blit = True	           | Optimizes rendering by only redrawing changed parts of the frame.
    # init_func = _init	     | Calls _init() once at the beginning to set up the animation.
    # repeat = False	       | The animation runs only once and does not loop.
    ani = animation.FuncAnimation(fig, _animate, np.arange(1, len(self.data('t'))), blit = True, init_func = _init, repeat = False)

    if file_path: 
      if mode == 'gif':
        ani.save(file_path, writer = 'imagemagick', fps = int(1 / self.dt))
      elif mode == 'mp4':
        ani.save(file_path, fps = int(1/self.dt), writer='avconv', codec='libx264')
    
    plt.show()
    # Clear the figure
    fig.clear()
    plt.close(fig)


  def render_axis(self, fig, ax):
    
    ax.grid(False)  # disable the grid
    dot, = ax.plot([], [], 'ro')
    time_text = ax.text(0.05, 0.9, '', transform = ax.transAxes)
    _position_list = self.data('position')[1]
    _dt = self.dt

    def _init():
      dot.set_data([], [])
      time_text.set_text('')
      return dot, time_text

    def _animate(i):
      x = _position_list[i]
      y = np.sin(3 * x)
      dot.set_data([x], [y])
      time_text.set_text("Time: " + str(np.round(i * _dt, 1)) + "s" + '\n' + "Frame: " + str(i))
      return dot, time_text

    ani = animation.FuncAnimation(fig, _animate
                                   , np.arange(1, len(self.data('t')))
                                   , blit = True, init_func = _init
                                   , repeat = False)
    
    return ani, dot


  def animate(self, file_path = './simulation_animate.gif', debug = False):

    from animation_tools import animateit 
    from IPython.display import Image

    # debug = False
    # # Get data
    # t_array = self.data('t')
    # x_array = self.data('position')[1]
    # dt = self.dt

    # inputs = [(i, x_array[i], dt) for i in range(len(t_array))]

    # if debug:
    #   frames = [render_frame(inp) for inp in inputs]
    # else: 
    #   # Parallel rendering
    #   with Pool() as pool:
    #     # frames = pool.map(render_frame, inputs)
    #     results = pool.map(square, range(10))

    # frames = animateit(self) 

    # Get data
    t_array = self.data('t')
    x_array = self.data('position')[1]
    dt = self.dt

    inputs = [(i, x_array[i], dt) for i in range(len(t_array))]

    if debug:
      frames = [render_frame(inp) for inp in inputs]
    else: 
      # Parallel rendering
      with Pool() as pool:
        frames = pool.map(render_frame, inputs)
        # frames = pool.map(square, range(10))

    # gifname = 'car_rl.gif'
    imageio.mimsave(file_path, frames, duration = 0.1, loop = 0)
    # c4d.gif(outfol, gifname, duration = 1)
    Image(file_path)  # doctest: +IGNORE_OUTPUT


  def _plot(self, ax, alpha = 0.4):
    
    # Plot init
    # fig = plt.figure()
    # ax = fig.add_subplot(111, autoscale_on = False, xlim = (-1.2, 0.5), ylim = (-1.1, 1.1))
    ax.grid(False)  # disable the grid
    # ax.set_facecolor((0, 1, 0, alpha))

    x = np.linspace(start = self.x_lim[0], stop = self.x_lim[1], num = 100)
    z = self.hx(x)
    ax.plot(x, z, color = '#003366')  # plot the sine wave
    ax.fill_between(x, ax.get_ylim()[0], z, color = '#9370DB', alpha = alpha)

    # plt.plot(x, y)
    # line, _ = ax.plot(x, y, 'o-', lw=2)
    xdata = np.array([self.p2x(s) for s in self.data('position')[1]])
    zdata = self.hx(xdata)

    ax.plot(xdata, zdata, 'b.', alpha = 0.3)
    indmaxx = np.argmax(xdata)
    ax.plot(xdata[indmaxx], zdata[indmaxx], 'bo')

    # plt.show()
    # plt.savefig(file_path)
    

  def push_right(self, x0, v0, plotlabel = ''):
    import matplotlib.pyplot as plt
    self.position = self.x2p(x0) 
    self.velocity = v0 

    # total_energy = []
    # time = []

    for _ in range(200): 
      self.step(2)

    x = [self.p2x(p) for p in self.data('position')[1]]
    plt.figure(10)
    plt.plot(x, label = plotlabel)
    plt.axhline(y = self.x_lim[1], color = 'g', linestyle = ':', label = 'goal')    
    plt.title(f"{self.mode}")
    plt.xlabel("samples")
    plt.ylabel("x")
    plt.grid(True)
    plt.gca().legend()

    plt.figure(20)
    plt.plot(self.data('velocity')[1], label = plotlabel)
    # plt.axhline(y = self.x_lim[1], color = 'g', linestyle = ':', label = 'goal')    
    plt.title(f"{self.mode}")
    plt.xlabel("samples")
    plt.ylabel("v")
    plt.grid(True)
    plt.gca().legend()

    
  def oscillate(self):
    self.store()
    import matplotlib.pyplot as plt
    # self.position = self.x2p(x0) 
    # self.velocity = v0 

    # total_energy = []
    # time = []
    # plt.switch_backend('qtagg') 
    # plt.ion()  # interactive mode

    fig, ax = plt.subplots()
    line, = ax.plot(np.nan, np.nan, 'o')
    ax.set_xlim(self.x_lim[0], self.x_lim[1])
    ax.set_ylim(-100, 100)

    from itertools import count
    cnt = count()
    while True: 
      print(next(cnt))


      if self.data('velocity')[1][-1] < 0:
        # previous velocity negative, 
        if self.velocity <= 0:
          # still negative, push left 
            action = 0
        else: 
          # now positive, push right
            action = 2
      else: 
        # previous velocity positive
        if self.velocity >= 0:
          # still positive, push right
          action = 2
        else: 
          # now negative, push left
          action = 0

      _, done = self.step(action)


      line.set_data([self.p2x(self.position)], [self.hx()]) 
      plt.pause(0.01)
      if done:
        break 
      

    
  def test_energy_balance(self, x0, v0):

    # from scipy import integrate
    
    PE_start = self.mass * self.gravity * (1 + self.hx(x0)) # add a baseline of 1 to avoid negative PE)
    KE_start = 0.5 * self.mass * v0**2
    # compute the path for the work of the engine

    # s, _ = integrate.quad(lambda xp: np.sqrt(1.0 + (self.steep_factor * np.cos(self.steep_factor * xp))**2), x, self.x_lim[1], epsabs = 1e-9, epsrel = 1e-9)
   
    W_engine = self.action_list[2] * (self.x2p(self.x_lim[1]) - self.x2p(x0)) # (self.x_lim[1] - x) # * np.cos(theta) # maybe we shouldnt project the path on x because the force is integrated along the entire path. 
    
    # Total available energy
    E_max = PE_start + KE_start + W_engine
    
    # goal energy 
    E_goal = self.mass * self.gravity * (1 + self.hx(self.x_lim[1]))

    print(f"Max reachable nrg: {E_max:.3f}, goal nrg: {E_goal:.3f}")
    print("Can reach goal?", E_max >= E_goal)


  def draw_track(self):
    ''' plot the trajectory of the mountain car environment (just the sine wave)'''
    import matplotlib.pyplot as plt

    x_vals = np.linspace(*self.x_lim, 500)
    h_vals = self.hx(x_vals)

    # Plot
    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, h_vals, lw = 2)
    plt.title(f"{self.mode}")
    plt.xlabel("x position")
    plt.ylabel("height")
    plt.grid(True)
    # plt.tight_layout()
    # plt.xlim(-200, 100)
    # plt.ylim(-200, 200)
    # plt.axis('equal')
    plt.show()




def plot_curve(data_list, filepath = "./my_plot.png"
                , x_label = "X", y_label = "Y", x_range = (0, 1)
                  , y_range = (0,1), color = "-r", kernel_size = 50, alpha = 0.4, grid = True):
  
  """ Plot a graph using matplotlib """

  if len(data_list) < 1:
    print("[WARNING] the data list is empty, no plot will be saved.")
    return
  

  fig = plt.figure()
  ax = fig.add_subplot(111) #, autoscale_on = False, xlim = x_range, ylim = y_range)
  ax.grid(grid)
  ax.set_xlabel(x_label)
  ax.set_ylabel(y_label)
  ax.plot(data_list, color, alpha=alpha)  # The original data is showed in background


  data_length = len(data_list)

  if data_length < kernel_size:
    kernel_size = len(data_list)

  # a uniform kernel of size 50 to smooth the graph by simple moving 
  # average averaging each point with kernal_size (50) neighbours. 
  kernel = np.ones(int(kernel_size))/float(kernel_size)  # Smooth the graph using a convolution. since it sums kernel_size items, it also have to divide by the same size to make average. 
  lower_boundary = kernel_size // 2
  upper_boundary = data_length - lower_boundary
  data_convolved_array = np.convolve(data_list, kernel, 'same')[lower_boundary:upper_boundary]


  #print("arange: " + str(np.arange(data_length)[lower_boundary:upper_boundary]))
  #print("Convolved: " + str(np.arange(data_length).shape))
  # totdata 283, lower 250, upper 33, datacovnoloved array [], 
  #         94,         250     -156                       94. 
  ax.plot(np.arange(data_length)[lower_boundary : upper_boundary], data_convolved_array, color, alpha = 1.0)  # Convolved plot
  
  if filepath: 
    fig.savefig(filepath)
    fig.clear()
    plt.close(fig)
    # print(plt.get_fignums())  # print the number of figures opened in background
  else: 
    plt.show() 


def axis_curve(data_list, ax
                , x_label = "X", y_label = "Y", x_range = (0, 1)
                  , y_range = (0,1), color = "-r", kernel_size = 50, alpha = 0.4, grid = True):
  
  """ Plot a graph using matplotlib """

  if len(data_list) < 1:
    print("[WARNING] the data list is empty, no plot will be saved.")
    return
  

  ax.grid(grid)
  ax.set_xlabel(x_label)
  ax.set_ylabel(y_label)
  ax.plot(data_list, color, alpha=alpha)  # The original data is showed in background


  data_length = len(data_list)

  if data_length < kernel_size:
    kernel_size = len(data_list)
    
  # a uniform kernel of size 50 to smooth the graph by simple moving 
  # average averaging each point with kernal_size (50) neighbours. 
  kernel = np.ones(int(kernel_size))/float(kernel_size)  # Smooth the graph using a convolution. since it sums kernel_size items, it also have to divide by the same size to make average. 
  lower_boundary = kernel_size // 2
  upper_boundary = data_length - lower_boundary
  data_convolved_array = np.convolve(data_list, kernel, 'same')[lower_boundary:upper_boundary]


  #print("arange: " + str(np.arange(data_length)[lower_boundary:upper_boundary]))
  #print("Convolved: " + str(np.arange(data_length).shape))
  # totdata 283, lower 250, upper 33, datacovnoloved array [], 
  #         94,         250     -156                       94. 
  ax.plot(np.arange(data_length)[lower_boundary : upper_boundary], data_convolved_array, color, alpha = 1.0)  # Convolved plot
  

def render_frame(i_data):
  i, x, dt = i_data

  # frames = []

  fig = plt.figure()
  canvas = FigureCanvas(fig)
  ax = fig.add_subplot(111, autoscale_on = False, xlim = (-1.2, 0.5), ylim = (-1.1, 1.1))
  ax.grid(False)  # disable the grid

  x_sin = np.linspace(start = -1.2, stop = 0.5, num = 100)
  y_sin = np.sin(3 * x_sin)
  ax.plot(x_sin, y_sin)  # plot the sine wave

  # for i in range(len(self..data('t'))):

  # x = self.data('position')[1][i]
  y = np.sin(3 * x)
  ax.plot(x, y, 'ro')
  ax.text(0.05, 0.9, "Time: " + str(np.round(i * dt, 1)) + "s" + '\n' + "Frame: " + str(i), transform = ax.transAxes)
  
  # plt.savefig(os.path.join(cache_dir, 'frame_{}.png'.format(i)), dpi = 100)    
  canvas.draw()
  buf = np.frombuffer(canvas.tostring_argb(), dtype = np.uint8)
  w, h = canvas.get_width_height()
  frame = buf.reshape((h, w, 4))

  # frames.append(frame)
  plt.close(fig)
  return frame

  # except Exception as e:
  #   print(f"Error at frame {i}: {e}")
  #   import traceback
  #   traceback.print_exc()
  #   return None














