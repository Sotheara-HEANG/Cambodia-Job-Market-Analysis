# DAX Measures for Clean PostgreSQL Views

Use these if you load the PostgreSQL views named:

- `public powerbi_jobs`
- `public powerbi_skills`
- `public powerbi_job_skills`

```DAX
Total Jobs = DISTINCTCOUNT('public powerbi_jobs'[job_id])
```

```DAX
Total Companies = DISTINCTCOUNT('public powerbi_jobs'[company_name])
```

```DAX
Total Locations = DISTINCTCOUNT('public powerbi_jobs'[location])
```

```DAX
Total Sources = DISTINCTCOUNT('public powerbi_jobs'[source_name])
```

```DAX
Average Salary USD = AVERAGE('public powerbi_jobs'[salary_avg])
```

```DAX
Jobs With Salary =
CALCULATE(
    DISTINCTCOUNT('public powerbi_jobs'[job_id]),
    NOT ISBLANK('public powerbi_jobs'[salary_avg])
)
```

```DAX
Salary Coverage % =
DIVIDE([Jobs With Salary], [Total Jobs])
```

```DAX
Total Job Skill Links = COUNTROWS('public powerbi_job_skills')
```

```DAX
Top Skill Job Count = DISTINCTCOUNT('public powerbi_job_skills'[job_id])
```

```DAX
Jobs Per Company =
DIVIDE([Total Jobs], [Total Companies])
```

```DAX
Entry Level Jobs =
CALCULATE(
    [Total Jobs],
    'public powerbi_jobs'[experience_level] = "Entry level"
)
```

```DAX
Senior Level Jobs =
CALCULATE(
    [Total Jobs],
    'public powerbi_jobs'[experience_level] = "Senior level"
)
```
