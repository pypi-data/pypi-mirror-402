from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from astropy.time import Time
from astropy.coordinates import get_sun
from astropy import units as u
from .utils.constants import J2, EARTH_EQUATORIAL_RADIUS as RE, GM_EARTH as MU


@dataclass
class Orbit:
    """
    轨道类，包含轨道参数和相关计算方法。

    Attributes:
        a: 轨道半长轴 (m)
        e: 轨道偏心率
        i: 轨道倾角 (rad)
        raan: 升交点赤经 (rad)
        arg_perigee: 近地点幅角 (rad)
        true_anomaly: 真近点角 (rad)
        time: 近地点时间 (datetime)
    """
    a: float
    e: float
    i: float
    raan: float
    arg_perigee: float
    true_anomaly: float
    time: datetime


def orbit_period(a: float) -> float:
    """
    根据轨道半长轴计算轨道周期

    Args:
        a: 轨道半长轴 (m)

    Returns:
        orbit_period: 轨道周期 (s)
    """
    # Kepler's Third laws of planetary motion
    return np.sqrt(4*np.pi**2 * a**3 / MU)


def raan_dot(a, e, i):
    """
    计算升交点赤经变化率
    参考 Curtis2020 2.45

    Args:
        a: 轨道半长轴 (m)
        e: 轨道偏心率
        i: 轨道倾角 (rad)

    Returns:
        raan_dot: 升交点赤经变化率 (rad/s)
    """

    raan_dot = (-1.5 * J2 * np.sqrt(MU) * RE**2 * np.cos(i) /
                (a**(7/2) * (1 - e**2)**2))

    return raan_dot


def orbit_normal(i: float, raan: float) -> np.ndarray:
    """
    计算轨道面法向量
    参考 Curtis2020 4.49

    Args:
        i: 轨道倾角 (rad)
        raan: 升交点赤经 (rad)

    Returns:
        n: 轨道面法向量 (np.ndarray)，单位矢量
    """

    n = np.array([
        np.sin(i) * np.sin(raan),
        -np.sin(i) * np.cos(raan),
        np.cos(i)
    ])

    return n


def beta_angle(h_hat: np.ndarray, s_hat: np.ndarray) -> float:
    """
    计算beta角

    注意，beta角定义为轨道面法向量与太阳矢量的夹角的补角，
    即 beta = 90° - angle(h_hat, s_hat)

    Args:
        h_hat: 轨道面法向量 (np.ndarray)，单位矢量
        s_hat: 太阳矢量 (np.ndarray)，单位矢量

    Returns:
        beta: beta角 (rad)
    """
    return np.arcsin(np.clip(np.dot(h_hat, s_hat), -1.0, 1.0))


def sunlight_time_per_orbit(a: float, beta: float) -> float:
    """
    计算卫星每轨道在阳光照射下的时间

    参考 Vallado 4ed, page 305

    Args:
        a: 轨道半长轴 (m)
        beta: beta角 (rad)

    Returns:
        t_sunlight: 每轨道阳光照射时间 (s)
    """

    # 日蚀半角

    if np.abs(np.sin(beta)) > RE/a:
        phi = 0
    else:
        phi = np.acos(np.sqrt(1-(RE/a)**2) / np.cos(beta))

    theta_eclipse = 2 * phi

    t_orbit = orbit_period(a)
    t_eclipse = theta_eclipse / (2*np.pi) * t_orbit
    t_sunlight = t_orbit - t_eclipse

    return t_sunlight


def beta_angle_and_sunlight_per_year(orbit_init: Orbit, year: int) -> list[tuple[datetime, float, float]]:
    """
    计算beta角和每轨道阳光照射时间

    Args:
        orbit_init: 初始轨道参数，包含轨道元素和近地点时间

    Returns:
        list of tuples: 每个元组包含(时间, beta角, 每轨道阳光照射时间)
    """

    t_orbit = Time(orbit_init.time, scale='ut1')
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    days = (end - start).days + 1

    results = []
    for i in range(days):
        t = start + timedelta(days=i)

        # 计算太阳矢量
        s = get_sun(Time(t))
        s_vec = s.cartesian.xyz.value
        s_hat = s_vec / np.linalg.norm(s_vec)

        # todo：此处未考虑真赤道与惯性系xy面的角度，需要改进
        raan_dot_value = raan_dot(orbit_init.a, orbit_init.e, orbit_init.i)
        raan = (orbit_init.raan + raan_dot_value
                * (Time(t).jd - t_orbit.jd) * 86400)

        beta = beta_angle(
            h_hat=orbit_normal(orbit_init.i, raan),
            s_hat=s_hat)

        sunlight_time = sunlight_time_per_orbit(orbit_init.a, beta)

        results.append((
            t,
            beta,
            sunlight_time))

    return results


def plot_beta_and_sunlight(results: list[tuple[datetime, float, float]]):
    """
    绘制beta角和每轨道阳光照射时间的曲线

    Args:
        results: beta_angle_and_sunlight_per_year 的输出结果

    Returns:
        fig: matplotlib figure object
    """
    import matplotlib.pyplot as plt

    times = [r[0] for r in results]
    betas = [np.rad2deg(r[1]) for r in results]
    sunlight_times = [r[2] / 60 for r in results]  # Convert to minutes

    fig = plt.figure(figsize=(10, 8))

    plt.subplot(2, 1, 1)
    plt.plot(times, betas, label='Beta Angle')

    # Mark max/min for Beta Angle
    max_beta = np.max(betas)
    min_beta = np.min(betas)
    max_beta_idx = np.argmax(betas)
    min_beta_idx = np.argmin(betas)

    plt.scatter([times[max_beta_idx]], [max_beta], color='red', zorder=5)
    plt.text(times[max_beta_idx], max_beta,
             f'Max: {max_beta:.2f}, {times[max_beta_idx].strftime("%Y-%m-%d")}', verticalalignment='bottom')

    plt.scatter([times[min_beta_idx]], [min_beta], color='green', zorder=5)
    plt.text(times[min_beta_idx], min_beta,
             f'Min: {min_beta:.2f}, {times[min_beta_idx].strftime("%Y-%m-%d")}', verticalalignment='top')

    plt.ylabel('Beta Angle (deg)')
    plt.title('Beta Angle vs Time')
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(times, sunlight_times, label='Sunlight Time', color='orange')

    # Mark max/min for Sunlight Time
    max_sun = np.max(sunlight_times)
    min_sun = np.min(sunlight_times)
    max_sun_idx = np.argmax(sunlight_times)
    min_sun_idx = np.argmin(sunlight_times)

    plt.scatter([times[max_sun_idx]], [max_sun], color='red', zorder=5)
    plt.text(times[max_sun_idx], max_sun,
             f'Max: {max_sun:.2f}, {times[max_sun_idx].strftime("%Y-%m-%d")}', verticalalignment='bottom')

    plt.scatter([times[min_sun_idx]], [min_sun], color='green', zorder=5)
    plt.text(times[min_sun_idx], min_sun,
             f'Min: {min_sun:.2f}, {times[min_sun_idx].strftime("%Y-%m-%d")}', verticalalignment='top')

    plt.ylabel('Sunlight Time (min)')
    plt.title('Sunlight Time vs Time')
    plt.xlabel('Time')
    plt.grid(True)

    plt.tight_layout()
    return fig


def raan_from_ltdn(epoch: datetime, ltdn_hours: float) -> float:
    """
    由降交点地方时计算升交点赤经 Ω

    Args:
        epoch: 计算时刻 (UTC 时间)
        ltdn_hours: 降交点地方时, 0~24 (小时)

    Returns:
        升交点赤经 RAAN Ω, 单位 rad, 0~2π
    """
    t = Time(epoch, scale="utc")

    # 1) LTDN -> LTAN
    ltan = (ltdn_hours + 12.0) % 24.0

    # 2) 太阳视赤经（apparent）
    sun = get_sun(t)  # GCRS
    alpha_sun = sun.ra.to(u.deg).value  # deg

    # 3) Ω = α_sun + 15°*(LTAN-12h)
    omega = alpha_sun + 15.0 * (ltan - 12.0)
    omega = omega % 360.0
    return np.deg2rad(omega)

def sso_inclination(a, e=0.0):
    """
    计算太阳同步轨道倾角

    Args:
        a: 轨道半长轴 (m)
        e: 轨道偏心率

    Returns:
        i: 轨道倾角 (rad)
    """
    raan_dot = 2 * np.pi / (365.25 * 86400)  # 太阳同步轨道升交点赤经变化率 (rad/s)
    k = (-1.5 * J2 * np.sqrt(MU) * RE**2 /
         (a**(7/2) * (1 - e**2)**2))

    cos_i = raan_dot / k
    i = np.arccos(cos_i)
    return i


def test_sso_inclination():
    """
    测试太阳同步轨道倾角计算函数
    """
    a = RE + 500e3  # 500 km高度轨道
    i = sso_inclination(a)
    print(f"SSO Inclination at 500 km: {np.rad2deg(i):.4f} degrees")


if __name__ == "__main__":
    # orbit = Orbit(
    #     a=6871030,
    #     e=0,
    #     i=np.deg2rad(97.3747),
    #     raan=np.deg2rad(79.8202),
    #     arg_perigee=0,
    #     true_anomaly=0,
    #     time=datetime(2025, 1, 1)
    # )

    # res = beta_angle_and_sunlight_per_year(orbit, 2025)

    # fig = plot_beta_and_sunlight(res)
    # fig.savefig("beta_sunlight_2025.png", dpi=300)

    # raan = raan_from_ltdn(datetime(2025, 12, 16, 0, 0, 0), 10.5)
    # print(raan)
    pass
