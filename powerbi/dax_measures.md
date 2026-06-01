# Starter DAX Measures

Create these measures in Power BI after loading the CSV files.

If you imported from PostgreSQL using Power BI's Navigator, your tables may be named like `public jobs`, `public job_skills`, and `public skills`. In that case, use the PostgreSQL formulas in the next section.

## CSV / Renamed Tables

```DAX
Total Jobs = DISTINCTCOUNT(jobs[job_id])
```

```DAX
Total Companies = DISTINCTCOUNT(jobs[company_name])
```

```DAX
Total Locations = DISTINCTCOUNT(jobs[location])
```

```DAX
Total Sources = DISTINCTCOUNT(jobs[source_name])
```

```DAX
Average Salary USD = AVERAGE(jobs[salary_avg])
```

```DAX
Jobs With Salary =
CALCULATE(
    DISTINCTCOUNT(jobs[job_id]),
    NOT ISBLANK(jobs[salary_avg])
)
```

```DAX
Salary Coverage % =
DIVIDE([Jobs With Salary], [Total Jobs])
```

```DAX
Total Job Skill Links = COUNTROWS(job_skills)
```

```DAX
Jobs Per Company =
DIVIDE([Total Jobs], [Total Companies])
```

```DAX
Entry Level Jobs =
CALCULATE(
    [Total Jobs],
    jobs[experience_level] = "Entry level"
)
```

```DAX
Senior Level Jobs =
CALCULATE(
    [Total Jobs],
    jobs[experience_level] = "Senior level"
)
```

```DAX
Top Skill Job Count = DISTINCTCOUNT(job_skills[job_id])
```

## PostgreSQL Navigator Tables

Use these when Power BI shows table names like `public jobs`.

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
