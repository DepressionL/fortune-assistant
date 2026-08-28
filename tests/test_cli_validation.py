"""CLI 输入校验测试：非法输入 → exit 2 + 可读报错（stderr）；合法输入 → exit 0。"""
from typer.testing import CliRunner

from fortune.cli import app

runner = CliRunner()


def _invoke(*args):
    return runner.invoke(app, list(args))


def test_bazi_invalid_date():
    r = _invoke("bazi", "-y", "1993", "-m", "2", "-d", "31", "-H", "13")
    assert r.exit_code == 2
    assert "输入错误" in r.output and "不存在" in r.output


def test_bazi_invalid_schools():
    r = _invoke("bazi", "-y", "1993", "-m", "3", "-d", "15", "-H", "9",
                "--schools", "wangshuai,bogus")
    assert r.exit_code == 2
    assert "非法流派" in r.output


def test_bazi_out_of_range():
    r = _invoke("bazi", "-y", "999", "-m", "3", "-d", "15", "-H", "9")
    assert r.exit_code == 2
    assert "超出支持范围" in r.output


def test_bazi_timezone_conversion():
    """--timezone 9：记录钟面时间按 UTC+9 理解，先换算 UTC+8 再校正。"""
    r = _invoke("bazi", "-y", "1993", "-m", "3", "-d", "15", "-H", "9", "-M", "30",
                "-g", "男", "--lng", "116.4", "--timezone", "9")
    assert r.exit_code == 0, r.output
    assert "时区 UTC+9 → UTC+8" in r.output
    assert "经度差" in r.output and "均时差" in r.output


def test_bazi_timezone_out_of_range():
    r = _invoke("bazi", "-y", "1993", "-m", "3", "-d", "15", "-H", "9", "--timezone", "20")
    assert r.exit_code == 2
    assert "时区" in r.output


def test_liuyao_invalid_month_zhi():
    r = _invoke("liuyao", "--backs", "1,1,1,1,1,1", "--month-zhi", "猫",
                "--day-ganzhi", "甲子")
    assert r.exit_code == 2
    assert "月建地支" in r.output


def test_liuyao_invalid_day_ganzhi_parity():
    r = _invoke("liuyao", "--backs", "1,1,1,1,1,1", "--month-zhi", "午",
                "--day-ganzhi", "甲丑")
    assert r.exit_code == 2
    assert "阴阳不相配" in r.output


def test_liuyao_bad_backs_count():
    r = _invoke("liuyao", "--backs", "1,2,3", "--month-zhi", "午",
                "--day-ganzhi", "甲子")
    assert r.exit_code == 2
    assert "恰好 6 个" in r.output


def test_liuyao_no_backs_no_random():
    r = _invoke("liuyao", "--month-zhi", "午", "--day-ganzhi", "甲子")
    assert r.exit_code == 2
    assert "--random" in r.output


def test_liuyao_random_ok():
    r = _invoke("liuyao", "--month-zhi", "午", "--day-ganzhi", "甲子", "--random")
    assert r.exit_code == 0
    assert "随机掷币" in r.output
    assert "断语" in r.output


def test_meihua_invalid_numbers():
    r = _invoke("meihua", "0", "34")
    assert r.exit_code == 2
    assert "正整数" in r.output


def test_meihua_numbers_ok_with_zhouyi():
    r = _invoke("meihua", "12", "34")
    assert r.exit_code == 0
    assert "卦辞" in r.output and "爻辞" in r.output
    assert "彖传" in r.output and "大象传" in r.output


def test_xiaoliuren_invalid_hour_zhi():
    r = _invoke("xiaoliuren", "--month", "5", "--day", "23", "--hour-zhi", "猫")
    assert r.exit_code == 2
    assert "时支" in r.output


def test_chenggu_female_warns():
    r = _invoke("chenggu", "-y", "1993", "-m", "3", "-d", "15", "-H", "9", "-g", "女")
    assert r.exit_code == 0
    assert "女命版判词未收录" in r.output
