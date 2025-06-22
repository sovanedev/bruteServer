import requests
import os
import uuid

BASE_URL = "http://localhost:8000"


def test_install_rule():
    dest = "/worker/rules"
    rule_filename = f"{uuid.uuid4()}.rule"
    rule_content = b"^d$123t\nsi1l$@\nr@u$2022\nd^D$2020\np1c$t\n^d$2022C\nD$!123\np1^d$456\nl$t2021\nlC$t!\nso0t^@123\nc$!@123\nu$456!\nt^d!\n^d$@t\n^d$!t\nr^p1c@\nt^2022l$\n^d$567C\n$@c\nse3c$\nse3c$456\nrC$\nso0t^@\nd$123!\n$456p1\nd$!@\ntC$2023\nsi2o5d$!\np1C#567\nr$909p1\n^d$909C\nsa@d$!t^d$2022c\nlD#2021\nsa@r^123\nc$@p1\nsi1t$!\nso0c$@\nsi1l$2023\nse0l$2023\nsa@d$2023!\nr$2023\np123u\n$123c\n^d$909!\nC^d@2021\nr^1u$@C\ntD$123!\n$!c\nr^1u\ndC!456\nsa@d$!\n$1$C$#$5$5$1"

    with open(rule_filename, "wb") as f:
        f.write(rule_content)

    with open(rule_filename, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/install-rule",
            data={"dest": dest},
            files={"rule": (rule_filename, f, "application/octet-stream")}
        )

    os.remove(rule_filename)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert rule_filename in data["saved_to"]

def test_install_base():
    dest = "/worker/bases"
    base_filename = f"{uuid.uuid4()}.dict"
    base_content = b"1iou23be9wbd\nh1892g89hdfs\n12h198g80hf\n1g9287gf879\n81g289dgb18wwd\nqw\nqwe\npenis\npeqisd\npeqis\npeqi1\np1C#550"

    with open(base_filename, "wb") as f:
        f.write(base_content)

    with open(base_filename, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/install-base",
            data={"dest": dest},
            files={"base": (base_filename, f, "application/octet-stream")}
        )

    os.remove(base_filename)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert base_filename in data["saved_to"]


def test_install_hash():
    id = f"{uuid.uuid4()}"
    payload = {
        "id": id,
        "hash": "bfb2ec07534c94ca75a2300c38df0fe6",
        "hash_type": 0,
        "dest": "/worker/hashes"
    }

    response = requests.post(f"{BASE_URL}/install-hash", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert id in data["saved_to"]


def test_hash_in_work():
    response = requests.get(f"{BASE_URL}/hash-in-work")

    assert response.status_code == 200
    data = response.json()
    print(data)
    assert "status" in data
    assert "servertime" in data
    assert "hashes" in data


test_install_rule()
test_install_base()
#test_install_hash()