import numpy as np
from . import constants


def sun_vector(jd_ut1: float) -> np.ndarray:
    """
    计算太阳在地心惯性坐标系下的矢量。

    Args:
        jd_ut1: UT1 时刻的儒略日

    Returns:
        太阳在地心惯性坐标系下的矢量。
    """
    # 参考 Vallado 4ed, ALGORITHM 29

    # Julian centuries since J2000.0
    t_ut1 = (jd_ut1 - 2_451_545.0) / 36_525.0

    #  mean longitude of the Sun
    lambda_sun_deg = 280.460 + 36_000.771 * t_ut1

    # Barycentric dynamical time, TDB
    t_tdb = t_ut1
    
    # mean anomaly for the Sun
    M_sun = 357.529_109_2 + 35_999.050_34 * t_tdb

    # ecliptic longitude of the Sun
    lambda_ecliptic_deg = (lambda_sun_deg
                           + 1.914_666_471 * np.sin(np.radians(M_sun))
                           + 0.019_994_643 * np.sin(np.radians(2 * M_sun)))

    # position magnitude in AU
    r_sun_norm_au = (1.000_140_612
                     - 0.016_708_617 * np.cos(np.radians(M_sun))
                     - 0.000_139_589 * np.cos(np.radians(2 * M_sun)))

    # Obliquity of the ecliptic（黄赤交角）
    epsilon_deg = 23.439_291 - 0.013_004_2 * t_tdb

    r_sun = np.array([
        np.cos(np.radians(lambda_ecliptic_deg)),   
        np.cos(np.radians(epsilon_deg)) * np.sin(np.radians(lambda_ecliptic_deg)),
        np.sin(np.radians(epsilon_deg)) * np.sin(np.radians(lambda_ecliptic_deg))
    ]) * r_sun_norm_au * constants.AU

    return r_sun
