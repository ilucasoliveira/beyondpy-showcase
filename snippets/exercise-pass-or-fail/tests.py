def _check(grade, verdict):
    output = run_with_inputs(grade)
    expected = f"Grade: {grade}\n{verdict}\n"
    if output == expected:
        return
    if verdict == "Passed" and "Failed" in output:
        advice = (
            "Every grade of 6 or more must give Passed: "
            "check the sign and the number in the condition."
        )
    elif verdict == "Failed" and "Passed" in output:
        advice = (
            "Every grade below 6 must give Failed, not just one of them: "
            "the condition needs to split the grades starting at 6."
        )
    else:
        advice = "Check the text: the output must match the expected one, letter by letter."
    raise AssertionError(
        f"With the grade {grade}, the expected output is {expected!r}, but got {output!r}. {advice}"
    )


def test_grade_seven_passes():
    """Grade 7: Passed"""
    _check("7", "Passed")


def test_grade_six_passes():
    """Grade 6 (the limit): Passed"""
    _check("6", "Passed")


def test_grade_ten_passes():
    """Grade 10: Passed"""
    _check("10", "Passed")


def test_grade_eight_passes():
    """Grade 8: Passed"""
    _check("8", "Passed")


def test_grade_five_fails():
    """Grade 5 (one point below the limit): Failed"""
    _check("5", "Failed")


def test_grade_four_fails():
    """Grade 4: Failed"""
    _check("4", "Failed")


def test_grade_zero_fails():
    """Grade 0: Failed"""
    _check("0", "Failed")
