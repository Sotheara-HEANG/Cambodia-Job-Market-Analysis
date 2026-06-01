SELECT 'jobs' AS table_name, COUNT(*) AS row_count FROM jobs
UNION ALL
SELECT 'skills' AS table_name, COUNT(*) AS row_count FROM skills
UNION ALL
SELECT 'job_skills' AS table_name, COUNT(*) AS row_count FROM job_skills;

SELECT source_name, COUNT(*) AS job_count
FROM jobs
GROUP BY source_name
ORDER BY job_count DESC;

SELECT job_category, COUNT(*) AS job_count
FROM jobs
GROUP BY job_category
ORDER BY job_count DESC;
