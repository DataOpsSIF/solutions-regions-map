COMMAND = """
SELECT
    solutionrewrites.short_name as 'solution_name',
    solutionrewrites.one_sentence_description as 'solution_description',
    CONCAT('https://solarimpulse.com/solutions-explorer/', solutionrewrites.slug) as solution_explorer,
    "Labelled" as "solution_status" ,
    solutions.solution_status_date as 'solution_date',
    companies.address,
    companies.geoLatitude,
    companies.geoLongitude,
    companies.country,
    companies.city,
    companies.name AS 'company_name',
    companies.about_us as 'about_company',
    companies.description as 'company_description'
FROM
    companies
left outer join solutions on companies.id = solutions.company_id
left outer join solutionrewrites on solutions.id = solutionrewrites.solution_id
WHERE companies.country = "France" and solutions.solution_status_id = 12
UNION
SELECT 
    solutionrewrites.short_name as 'solution_name',
    solutionrewrites.one_sentence_description as 'solution_description',
    CONCAT('https://solarimpulse.com/solutions-explorer/', solutionrewrites.slug) as solution_explorer,
        CASE 
        WHEN is_labeled = 1 THEN 'Labelled'
        WHEN is_labeled IS NULL AND is_listed = 1 THEN 'Listed'
    END AS 'solution_status',
    ssfs.ssf_status_date as 'solution_date',
    companies.address,
    companies.geoLatitude,
    companies.geoLongitude,
    companies.country,
    companies.city,
    companies.name AS 'company_name',
    companies.about_us as 'about_company',
    companies.description as 'company_description'
FROM
    companies
left outer join ssfs on companies.id = ssfs.company_id
left outer join solutionrewrites on ssfs.id = solutionrewrites.ssf_id
WHERE companies.country = "France" and (ssfs.is_labeled = 1 OR ssfs.is_listed = 1)
"""
