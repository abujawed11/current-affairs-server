def compute_score(correct_flags: list[bool]) -> tuple[int, int, float]:
    total = len(correct_flags)
    score = sum(1 for v in correct_flags if v)
    accuracy = round((score / total) * 100.0, 2) if total else 0.0
    return score, total, accuracy
