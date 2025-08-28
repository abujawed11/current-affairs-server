# def compute_score(correct_flags: list[bool]) -> tuple[int, int, float]:
#     total = len(correct_flags)
#     score = sum(1 for v in correct_flags if v)
#     accuracy = round((score / total) * 100.0, 2) if total else 0.0
#     return score, total, accuracy



def compute_score(correct_flags: list[bool], answered_flags: list[bool]) -> tuple[float, int, float]:
      """
      Compute score with negative marking:
      - Correct answer: +1 mark
      - Wrong answer: -0.5 marks
      - Unattempted: 0 marks

      Args:
          correct_flags: List of True/False for each question (True if correct)
          answered_flags: List of True/False for each question (True if attempted)

      Returns:
          (score, total_questions, accuracy_percentage)
      """
      total_questions = len(correct_flags)
      score = 0.0
      attempted_count = 0
      correct_count = 0

      for i in range(total_questions):
          if answered_flags[i]:  # Question was attempted
              attempted_count += 1
              if correct_flags[i]:  # Correct answer
                  score += 1.0
                  correct_count += 1
              else:  # Wrong answer
                  score -= 0.5
          # Unattempted questions add 0 (no change to score)

      # Calculate accuracy based on attempted questions only
      if attempted_count > 0:
          accuracy_pct = (correct_count / attempted_count) * 100
      else:
          accuracy_pct = 0.0

      return score, total_questions, accuracy_pct