import requests
import json
import matplotlib.pyplot as plt
from datetime import datetime
import pymsis


def plot_f10_7():
    """
    读取本地json文件，绘制time-tag vs predicted_f10.7曲线
    """

    with open("predicted-solar-cycle.json", "r", encoding="utf-8") as f:
        predicted_data = json.load(f)

    with open("f10-7cm-flux-smoothed.json", "r", encoding="utf-8") as f:
        historical_data = json.load(f)


    predicted_time_tags = [datetime.strptime(item["time-tag"], "%Y-%m") for item in predicted_data]
    predicted_f10_7 = [item["predicted_f10.7"] for item in predicted_data]

    historical_time_tags = [datetime.strptime(item["time-tag"], "%Y-%m") for item in historical_data]
    historical_f10_7 = [item["f10.7"] for item in historical_data]
    
    historical_smoothed_data = [item for item in historical_data if item["smoothed_f10.7"] != -1]
    historical_smoothed_time_tags = [datetime.strptime(item["time-tag"], "%Y-%m") for item in historical_smoothed_data]
    historical_smoothed_f10_7 = [item["smoothed_f10.7"] for item in historical_smoothed_data]


    # 为了避免x轴标签过于拥挤，可以每隔几个点显示一个标签，或者旋转标签
    plt.figure(figsize=(12, 6))
    plt.plot(predicted_time_tags, predicted_f10_7, label="Predicted F10.7", marker='.')
    plt.plot(historical_time_tags, historical_f10_7, label="Historical F10.7", marker='.')
    plt.plot(historical_smoothed_time_tags, historical_smoothed_f10_7, label="Historical Smoothed F10.7", marker='.')
    
    plt.xlabel("Time")
    plt.ylabel("F10.7")
    plt.title("Solar Cycle F10.7 Flux")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def F10_7():
    """
    获取F10.7太阳活动指数的示例函数

    Returns:
        f10_7: F10.7太阳活动指数
    """

    # 预测数据
    url = "https://services.swpc.noaa.gov/json/solar-cycle/predicted-solar-cycle.json"
    response = requests.get(url)
    with open("predicted-solar-cycle.json", "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=4, ensure_ascii=False)

    # 历史数据
    url = "https://services.swpc.noaa.gov/json/solar-cycle/f10-7cm-flux-smoothed.json"
    response = requests.get(url)
    with open("f10-7cm-flux-smoothed.json", "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=4, ensure_ascii=False)

    print("下载完成")


if __name__ == "__main__":
    # F10_7()
    # plot_f10_7()

    import numpy as np
    import pymsis

    dates = np.arange(np.datetime64("2026-10-28T00:00"), np.datetime64("2030-11-04T00:00"), np.timedelta64(30, "m"))
    # geomagnetic_activity=-1 is a storm-time run

    # aps = np.full(len(dates), 4.0)  # 或 5–7
    data = pymsis.calculate(
        dates = np.datetime64("2026-10-28T00:00"), 
        lons=0, 
        lats=0, 
        alts=400, 
        f107s=150,
        f107as=150,
        aps=4)

    
    print(data)

