"""client for testing"""

import requests

if __name__ == "__main__":
    server = "https://delismm.nimbus.dlr.de/"
    surrogateName = "tank_isotensoid_frpMass[kg]_v_1.0"

    print("############ Surrogate list #############")
    endpoint = "list_surrogates"
    request = f"{server}/{endpoint}"
    r = requests.get(request)
    print(request, r.status_code, r.text)

    print("############ Surrogate info #############")
    endpoint = f"surrogate_info/{surrogateName}"
    request = f"{server}/{endpoint}"
    r = requests.get(request)
    print(request, r.status_code, r.text)

    print("############ Surrogate call #############")
    parameters = ["2000", "1000", "0.5"]  # dcyl, lcyl, pressure
    request = (
        f"https://delismm.nimbus.dlr.de/call/?surrogate_name={surrogateName}&"
        f"parameters={parameters[0]}&parameters={parameters[1]}&parameters={parameters[2]}"
    )
    r = requests.get(request)
    print(request, r.status_code, r.text)


if __name__ == "__main__":
    from delismm.api import getSurrogate

    surrogateName = "tank_isotensoid_frpMass[kg]_v_1.0"
    s = getSurrogate(surrogateName)
    p = [2000, 1000, 0.5]
    print(s(p))
