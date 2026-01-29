import pandas as pd
import numpy as np
import spheresmooth as ss
import geopandas as gpd
import matplotlib.pyplot as plt

# ----------------------------------------------------
# 1. Load APW spherical data (already packaged)
# ----------------------------------------------------
apw = ss.load_apw()     # pandas DataFrame
# columns: [t, theta, phi]

t = apw.iloc[:, 0].values
spherical = apw.iloc[:, 1:3].values   # theta (colatitude), phi (longitude)

# ----------------------------------------------------
# 2. spherical → cartesian
# ----------------------------------------------------
apw_cartesian = ss.spherical_to_cartesian(spherical)

# ----------------------------------------------------
# 3. Quantile knots
# ----------------------------------------------------
dimension = 15
initial_knots = ss.knots_quantile(t, dimension)

# lambda sequence
lambda_seq = np.exp(np.linspace(np.log(1e-7), np.log(1), 40))

# ----------------------------------------------------
# 4. Penalized spherical spline fit
# ----------------------------------------------------
fit = ss.penalized_linear_spherical_spline(
    t=t,
    y=apw_cartesian,
    dimension=dimension,
    initial_knots=initial_knots,
    lambdas=lambda_seq
)

bic_list = fit["bic_list"]
fits = fit["fits"]

best_index = np.argmin(bic_list)
best_fit = fits[best_index]
control_points = best_fit["control_points"]
knots = best_fit["knots"]

print("Best λ index:", best_index)
print("Control points (cartesian):")
print(control_points)

# ----------------------------------------------------
# 5. Convert control points → (theta, phi)
# ----------------------------------------------------
cp_spherical = ss.cartesian_to_spherical(control_points)
cp_deg = np.degrees(cp_spherical)

# convert to latitude/longitude
cp_df = pd.DataFrame({
    "latitude": 90 - cp_deg[:, 0],
    "longitude": cp_deg[:, 1]
})

# ----------------------------------------------------
# 6. Geodesic curve fitting
# ----------------------------------------------------
ts = np.linspace(0, 1, 2000)

curve_cart = ss.piecewise_geodesic(ts, control_points, knots)
curve_sph = ss.cartesian_to_spherical(curve_cart)
curve_deg = np.degrees(curve_sph)

curve_df = pd.DataFrame({
    "latitude": 90 - curve_deg[:, 0],
    "longitude": curve_deg[:, 1]
})

# ----------------------------------------------------
# 7. Original APW data → (lat, lon)
# ----------------------------------------------------
apw_deg = np.degrees(spherical)

apw_df = pd.DataFrame({
    "latitude": 90 - apw_deg[:, 0],
    "longitude": apw_deg[:, 1]
})

# Convert to GeoDataFrame
g_apw = gpd.GeoDataFrame(apw_df,
                         geometry=gpd.points_from_xy(apw_df.longitude, apw_df.latitude),
                         crs="EPSG:4326")

g_cp = gpd.GeoDataFrame(cp_df,
                        geometry=gpd.points_from_xy(cp_df.longitude, cp_df.latitude),
                        crs="EPSG:4326")

g_curve = gpd.GeoDataFrame(curve_df,
                           geometry=gpd.points_from_xy(curve_df.longitude, curve_df.latitude),
                           crs="EPSG:4326")

# ----------------------------------------------------
# 8. World map
# ----------------------------------------------------
url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
world = gpd.read_file(url)

fig, ax = plt.subplots(figsize=(12, 8))

world.plot(ax=ax, color="antiquewhite", edgecolor="grey")
g_apw.plot(ax=ax, markersize=3)
g_cp.plot(ax=ax, markersize=50, color="blue", marker="s")
g_curve.plot(ax=ax, markersize=1, color="red")

ax.set_xlabel("longitude")
ax.set_ylabel("latitude")

plt.title("APW Data + Control Points + Fitted Spherical Spline")
plt.show()
