# DAX Measures for PostgreSQL Imports

Use this file when Power BI shows table names like `public jobs`.

```DAX
Total Jobs = DISTINCTCOUNT('public jobs'[job_id])
```

```DAX
Total Companies = DISTINCTCOUNT('public jobs'[company_name])
```

```DAX
Total Locations = DISTINCTCOUNT('public jobs'[location])
```

```DAX
Total Sources = DISTINCTCOUNT('public jobs'[source_name])
```

```DAX
Average Salary USD = AVERAGE('public jobs'[salary_avg])
```

```DAX
Jobs With Salary =
CALCULATE(
    DISTINCTCOUNT('public jobs'[job_id]),
    NOT ISBLANK('public jobs'[salary_avg])
)
```

```DAX
Salary Coverage % =
DIVIDE([Jobs With Salary], [Total Jobs])
```

```DAX
Total Job Skill Links = COUNTROWS('public job_skills')
```

```DAX
Jobs Per Company =
DIVIDE([Total Jobs], [Total Companies])
```

```DAX
Entry Level Jobs =
CALCULATE(
    [Total Jobs],
    'public jobs'[experience_level] = "Entry level"
)
```

```DAX
Senior Level Jobs =
CALCULATE(
    [Total Jobs],
    'public jobs'[experience_level] = "Senior level"
)
```

```DAX
Top Skill Job Count = DISTINCTCOUNT('public job_skills'[job_id])
```

## Alternative

Rename `public jobs` to `jobs`, `public job_skills` to `job_skills`, and `public skills` to `skills` in Power BI. Then use `dax_measures.md` formulas from the CSV / renamed tables section.
