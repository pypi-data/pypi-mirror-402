import numpy as np
import plotly.graph_objects as go
from spheresmooth import (
    spherical_to_cartesian,
    cartesian_to_spherical,
    spherical_dist,
    piecewise_geodesic,
    penalized_linear_spherical_spline,
    geodesic
)

c = 1/np.sqrt(3)
control_points = np.array([
    [ c,  c,  c],
    [ c,  c, -c],
    [-c,  c,  c],
    [-c,  c, -c]
])
knots = np.array([1, 2, 3, 3.5]) 

# --- compute curve ---
t = np.linspace(0, 4, 200)
curve = piecewise_geodesic(t, control_points, knots)


# --- sphere mesh ---
u = np.linspace(0, 2*np.pi, 60)
v = np.linspace(0, np.pi, 30)
x = np.outer(np.cos(u), np.sin(v))
y = np.outer(np.sin(u), np.sin(v))
z = np.outer(np.ones_like(u), np.cos(v))

# --- plot ---
fig = go.Figure()

fig.update_layout(
    scene=dict(aspectmode='data'),
    title="Sphere with Latitude/Longitude Lines"
)

fig.add_surface(x=x, y=y, z=z, opacity=0.1, colorscale="Greys")

fig.add_trace(go.Scatter3d(
    x=control_points[:,0],
    y=control_points[:,1],
    z=control_points[:,2],
    mode='markers',
    marker=dict(size=4, color='blue')
))

fig.add_trace(go.Scatter3d(
    x=curve[:,0],
    y=curve[:,1],
    z=curve[:,2],
    mode='lines',
    line=dict(color='red', width=5)
))

# ----- Latitude lines (위도선) -----
lat_values = np.linspace(-60, 60, 8)  # degrees

for lat in lat_values:
    phi = np.radians(lat)
    u = np.linspace(0, 2*np.pi, 200)
    x_lat = np.cos(u) * np.cos(phi)
    y_lat = np.sin(u) * np.cos(phi)
    z_lat = np.ones_like(u) * np.sin(phi)

    fig.add_trace(go.Scatter3d(
        x=x_lat, y=y_lat, z=z_lat,
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False
    ))

# ----- Longitude lines (경도선) -----
lon_values = np.linspace(0, 330, 10)  # degrees

for lon in lon_values:
    lam = np.radians(lon)
    v = np.linspace(-np.pi/2, np.pi/2, 200)
    x_lon = np.cos(v) * np.cos(lam)
    y_lon = np.cos(v) * np.sin(lam)
    z_lon = np.sin(v)

    fig.add_trace(go.Scatter3d(
        x=x_lon, y=y_lon, z=z_lon,
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False
    ))


fig.update_layout(
    scene=dict(aspectmode='data'),
    title="Piecewise Geodesic on Sphere"
)

fig.show()
