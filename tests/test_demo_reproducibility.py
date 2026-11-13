from mockr_coach.cli import main


def test_demo_stdout_is_repeatable(capsys):
    assert main(["demo"]) == 0
    first = capsys.readouterr().out
    assert main(["demo"]) == 0
    assert capsys.readouterr().out == first
