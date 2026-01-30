"""重力梯度力矩分析"""
import numpy as np
from .utils import lib
from .utils.constants import GM_EARTH, EARTH_EQUATORIAL_RADIUS as R_EARTH
from .pyIGRF14.igrf import get_mag_field


def gen_sphere_unit_vector_list() -> list[np.ndarray]:
    """
    生成球面单位矢量列表

    Returns:
        球面单位矢量列表
    """
    n = []
    for lat in range(-90, 90, 5):
        for lon in range(0, 360, 5):
            n.append(lib.sphere_unit_vector(np.deg2rad(lat), np.deg2rad(lon)))

    return n


def calc_gravity_gradient_torque(inertia: np.ndarray, r: float, n: np.ndarray) -> np.ndarray:
    """
    计算重力梯度力矩。

    参考：Markley 2014 (p104 eq. 3.155)

    Args:
        inertia: 本体系惯量矩阵 (3x3 矩阵, kg·m²)
        r: 质心到地心的距离 (m)
        n: 引力方向在本体系的表示（单位矢量）, 无量纲

    Returns:
        torque: 重力梯度力矩矢量
    """

    # 确保 I 是 3x3 矩阵
    assert inertia.shape == (3, 3), "I must be a 3x3 matrix"

    # 单位化
    n = lib.unit_vector(n)

    # 计算重力梯度力矩
    torque = (3 * GM_EARTH / r**3) * np.cross(n, inertia@n)

    return torque


def get_max_gravity_gradient_torque(inertia: np.ndarray, r: float) -> float:
    """
    计算重力梯度力矩最大值

    Args:
        inertia: 本体系惯量矩阵 (3x3 矩阵, kg·m²)
        r: 质心到地心的距离 (m)

    Returns:
        max_torque: 重力梯度力矩最大值 (Nm)
    """
    n_list = gen_sphere_unit_vector_list()

    torque_norms = [np.linalg.norm(
        calc_gravity_gradient_torque(inertia, r, n)) for n in n_list]

    max_torque = float(max(torque_norms))

    return max_torque


def B_max_at_altitude(h_m: float) -> float:
    """
    磁场最大值随高度变化的近似估计

    Args:
        h_m : Altitude above Earth's surface in m.

    Returns:
        Estimated maximum field magnitude at altitude in tesla (T).
    """
    if h_m < 0:
        raise ValueError("h_m must be >= 0")

    # 地表磁场最大值约为 65 µT，
    # 见 fig 1, https://link.springer.com/article/10.1186/s40623-020-01288-x
    # https://www.ncei.noaa.gov/products/international-geomagnetic-reference-field
    B0_T: float = 65.0e-6  # 65 µT at Earth's surface

    ratio = R_EARTH / (R_EARTH + h_m)
    return B0_T * (ratio ** 3)


def print_B_max_table():
    """
    Print a table of maximum geomagnetic field magnitudes at various altitudes.
    """
    altitudes_m = [0, 100e3, 200e3, 400e3, 500e3, 800e3,
                   1000e3, 2000e3, 5000e3, 10000e3, 20000e3, 35786e3]

    print(f"{'h (km)':>8} | {'B_max (µT)':>10} | {'B_max (nT)':>12}")
    print("-" * 38)
    for h in altitudes_m:
        B_T = B_max_at_altitude(h)
        B_nT = B_T * 1e9
        print(f"{h/1000:8.0f} | {B_T*1e6:10.3f} | {B_nT:12.1f}")


def residual_magnetic_torque(residual_magnetic_moment: float, h: float) -> float:
    """
    计算卫星剩磁矩产生的力矩

    Args:
        residual_magnetic_moment: 剩磁矩 (A·m²)
        h: 高度 (m)

    Returns:
        torque: 剩磁矩产生的力矩 (Nm)
    """
    # 典型值，实际应用中应根据具体情况调整
    mag_field = B_max_at_altitude(h)  # 磁场强度 (T)
    torque = residual_magnetic_moment * mag_field  # Nm

    return torque


def thruster_torque(thruster_force: float, lever_arm: float) -> float:
    """
    计算推进器产生的力矩

    Args:
        thruster_force: 推进器推力 (N)
        lever_arm: 力臂长度 (m)

    Returns:
        torque: 推进器产生的力矩 (Nm)
    """
    torque = thruster_force * lever_arm
    return torque


# 用于测试
# 在 src 目录下执行以下命令
# py -m aocs_lab.gravity_gradient_torque
if __name__ == '__main__':
    I = np.array([[89, 19, -7],
                  [19, 341, 2],
                  [-7, 2, 294]])

    print(f"最大重力梯度力矩为: {get_max_gravity_gradient_torque(I, 6900e3):.1e} Nm")

    print_B_max_table()

    residual_magnetic_torque_value = residual_magnetic_torque(2, 500e3)
    print(f"高度 500 km 处，剩磁矩 2 A·m² 产生的力矩约为: {residual_magnetic_torque_value:.1e} Nm")

    thruster_torque_value = thruster_torque(0.015, 0.03)
    print(f"推进器推力 0.015 N，力臂 0.03 m 产生的力矩约为: {thruster_torque_value:.1e} Nm")