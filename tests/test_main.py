from complaint_intelligence.__main__ import main


def test_main_reports_current_project_status(capsys) -> None:
    main()

    output = capsys.readouterr().out
    assert "Status: implemented locally" in output
    assert "tfidf_logistic_regression" in output
    assert "Financial_Complaint_Intelligence.pbix" in output
    assert "no trained model yet" not in output
