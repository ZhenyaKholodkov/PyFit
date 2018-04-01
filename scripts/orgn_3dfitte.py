import numpy as np
import scipy.linalg
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

# Import plotly package
import plotly
import plotly.graph_objs as go

# Check ploltly version
plotly.__version__

# To communicate with Plotly's server, sign in with credentials file
import plotly.plotly as py
plotly.tools.set_credentials_file(username='pyfit.mail', api_key='QFsZPXhilMSF2knxfDhi')

# Create data with x and y random over [-2, 2], and z a Gaussian function of x and y.
np.random.seed(12345)
x = 2 * (np.random.random(500) - 0.5)
y = 2 * (np.random.random(1000) - 0.5)


def f(x, y):
    return np.exp(-(x + y[:500] ** 2))


z = f(x, y)

data = np.c_[x, y, z]

# regular grid covering the domain of the data
mn = np.min(data, axis=0)
mx = np.max(data, axis=0)
X, Y = np.meshgrid(np.linspace(mn[0], mx[0], 20), np.linspace(mn[1], mx[1], 20))
XX = X.flatten()
YY = Y.flatten()

# best-fit quadratic curve (2nd-order)
A = np.c_[np.ones(data.shape[0]), data[:, :2], np.prod(data[:, :2], axis=1), data[:, :2] ** 2]
C, _, _, _ = scipy.linalg.lstsq(A, data[:, 2])

# evaluate it on a grid
Z = np.dot(np.c_[np.ones(XX.shape), XX, YY, XX * YY, XX ** 2, YY ** 2], C).reshape(X.shape)

# plot points and fitted surface using Matplotlib
fig = plt.figure(figsize=(10, 10))
ax = fig.gca(projection='3d')
ax.plot_surface(X, Y, Z, rstride=1, cstride=1, alpha=0.2)
ax.scatter(data[:,0], data[:,1], data[:,2], c='r', s=50)
plt.xlabel('X')
plt.ylabel('Y')
ax.set_zlabel('Z')
ax.axis('equal')
ax.axis('tight')

# plot points and fitted surface using Plotly
trace3 = go.Surface(
    z=Z,
    x=X,
    y=Y,
    colorscale='RdBu',
    opacity=0.999
)

# plot points and fitted surface using Plotly
trace1 = go.Scatter3d(
    x=data[:,0],
    y=data[:,1],
    z=data[:,2],
    mode='markers',
    marker=dict(size=4, color='red', line=dict(color='black', width=0.5), opacity=0.8)
)

trace2 = go.Surface(z=Z, x=X, y=Y, colorscale='RdBu', opacity=0.999)

# Dictionary of style options for all axes
axis = dict(
    showbackground=True, # show axis background
    backgroundcolor="rgb(204, 204, 204)", # set background color to grey
    gridcolor="rgb(255, 255, 255)",       # set grid line color
    zerolinecolor="rgb(255, 255, 255)",   # set zero grid line color
)

# Package the trace dictionary into a data object
data_test2 = go.Data([trace1, trace3])

# Make a layout object
layout = go.Layout(
    title='2nd-order (quadratic) surface', # set plot title
    scene=go.Scene(  # axes are part of a 'scene' in 3d plots
        xaxis=go.XAxis(axis), # set x-axis style
        yaxis=go.YAxis(axis), # set y-axis style
        zaxis=go.ZAxis(axis)),  # set z-axis style
)

# Make a figure object
fig = go.Figure(data=data_test2, layout=layout)

# Send to Plotly and show in notebook
py.plot(fig, filename='test2')