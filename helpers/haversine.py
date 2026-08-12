import numpy as np

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000

    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)

    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2)**2

    return 2 * R * np.atan2(np.sqrt(a), np.sqrt(1 - a))