from engine import run, main


def test_run_returns_status_message():
    assert run() == "CFT-ENGINE0 engine is running."


def test_main_prints_status_message(capsys):
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "CFT-ENGINE0 engine is running."
