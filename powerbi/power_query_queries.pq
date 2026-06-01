// Power BI Power Query M setup for this local project.
// In Power BI Desktop:
// 1. Home > Transform data > New source > Blank query
// 2. Advanced Editor
// 3. Paste one query at a time, or adapt these shared queries in Power Query.
//
// Project root on this machine:
// D:\Documents\itc_files\Year_04_Semester_02\Data Visualization\Job_Market_Demand\job-market-analysis

section JobMarketDemand;

shared ProjectRoot =
    "D:\Documents\itc_files\Year_04_Semester_02\Data Visualization\Job_Market_Demand\job-market-analysis";

shared LoadCsv = (relativePath as text) as table =>
    let
        Source = Csv.Document(
            File.Contents(ProjectRoot & "\" & relativePath),
            [
                Delimiter = ",",
                Encoding = 65001,
                QuoteStyle = QuoteStyle.Csv
            ]
        ),
        PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
    in
        PromotedHeaders;

shared jobs =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\jobs.csv"),
        {
            {"job_id", type text},
            {"source_name", type text},
            {"job_title", type text},
            {"job_category", type text},
            {"company_name", type text},
            {"location", type text},
            {"salary", type text},
            {"salary_min", type number},
            {"salary_max", type number},
            {"salary_avg", type number},
            {"salary_currency", type text},
            {"employment_type", type text},
            {"experience_level", type text},
            {"job_description", type text},
            {"skills", type text},
            {"date_posted", type date},
            {"source_url", type text},
            {"scraped_at", type datetime}
        }
    );

shared skills =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\skills.csv"),
        {
            {"skill_id", Int64.Type},
            {"skill_name", type text}
        }
    );

shared job_skills =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\job_skills.csv"),
        {
            {"job_id", type text},
            {"skill_id", Int64.Type},
            {"skill", type text}
        }
    );

shared location_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\location_summary.csv"),
        {
            {"location", type text},
            {"job_count", Int64.Type},
            {"company_count", Int64.Type},
            {"average_salary_usd", type number}
        }
    );

shared source_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\source_summary.csv"),
        {
            {"source_name", type text},
            {"job_count", Int64.Type},
            {"company_count", Int64.Type},
            {"category_count", Int64.Type},
            {"average_salary_usd", type number}
        }
    );

shared category_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\category_summary.csv"),
        {
            {"job_category", type text},
            {"job_count", Int64.Type},
            {"company_count", Int64.Type},
            {"location_count", Int64.Type},
            {"average_salary_usd", type number}
        }
    );

shared skill_demand_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\skill_demand_summary.csv"),
        {
            {"skill_id", Int64.Type},
            {"skill", type text},
            {"job_count", Int64.Type}
        }
    );

shared company_hiring_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\company_hiring_summary.csv"),
        {
            {"company_name", type text},
            {"job_count", Int64.Type},
            {"unique_locations", Int64.Type},
            {"unique_categories", Int64.Type},
            {"average_salary_usd", type number}
        }
    );

shared salary_summary =
    Table.TransformColumnTypes(
        LoadCsv("data\powerbi\salary_summary.csv"),
        {
            {"summary_type", type text},
            {"category", type text},
            {"job_count", Int64.Type},
            {"salary_min_avg", type number},
            {"salary_max_avg", type number},
            {"salary_avg", type number}
        }
    );
