# Seeds

Place your quiz JSON files here and import them into MySQL.

## JSON shape (single test per file)

```json
{
  "title": "Current Affairs – 26 Aug 2025 (Daily)",
  "duration_sec": 1200,
  "questions": [
    {
      "date": "2025-08-26",
      "category": "Economy",
      "stem": "Which body released the latest CPI inflation data for India?",
      "explanation": "CPI is released by the National Statistical Office (NSO).",
      "options": [
        { "text": "Reserve Bank of India", "is_correct": false },
        { "text": "Ministry of Finance", "is_correct": false },
        { "text": "National Statistical Office", "is_correct": true },
        { "text": "NITI Aayog", "is_correct": false }
      ]
    }
  ]
}
