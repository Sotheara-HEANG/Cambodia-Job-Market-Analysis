// Power BI Power Query M setup for direct PostgreSQL connection.
// Update ServerName and DatabaseName if your .env uses different values.

section JobMarketDemandPostgreSQL;

shared ServerName = "localhost:5433";
shared DatabaseName = "cambodia_job_market_analysis";
shared Source = PostgreSQL.Database(ServerName, DatabaseName);

shared powerbi_jobs = Source{[Schema = "public", Item = "powerbi_jobs"]}[Data];
shared powerbi_skills = Source{[Schema = "public", Item = "powerbi_skills"]}[Data];
shared powerbi_job_skills = Source{[Schema = "public", Item = "powerbi_job_skills"]}[Data];

shared location_summary = Source{[Schema = "public", Item = "location_summary"]}[Data];
shared source_summary = Source{[Schema = "public", Item = "source_summary"]}[Data];
shared category_summary = Source{[Schema = "public", Item = "category_summary"]}[Data];
shared skill_demand_summary = Source{[Schema = "public", Item = "skill_demand_summary"]}[Data];
shared company_hiring_summary = Source{[Schema = "public", Item = "company_hiring_summary"]}[Data];
shared salary_summary = Source{[Schema = "public", Item = "salary_summary"]}[Data];
