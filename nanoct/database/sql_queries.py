
base_testcase_query = """
SELECT * ,
    ROUND((julianday(completed_at) - julianday(started_at)) * 86400) as duration,
    '{hash_value}' as hash,
    (strftime('%s', started_at) + 30) * 1000 AS started_at_unix,
    (strftime('%s', completed_at) + 10) * 1000 AS completed_at_unix,
    CASE 
        WHEN status = 'FAIL'
            THEN 'https://raw.githubusercontent.com/gr0vity-dev/nano-node-builder/main/continuous_testing/' || '{hash_value}' || '_' || testcase || '.txt'
        ELSE NULL 
    END AS log
FROM testcases 
WHERE sql_id in (
select link_sql_id from mappings where main_sql_id in (select sql_id from builds where hash = '{hash_value}') and link_type = 'testcases' )
ORDER BY testcase
"""
base_query_template = """
WITH CTE AS (
    SELECT 
        b.pull_request,
        b.build_started_at,
        b.hash,
        b.type,
        -- Calculate revision for pull_request type
        CASE 
            WHEN b.type = 'pull_request' THEN ROW_NUMBER() OVER(PARTITION BY b.pull_request, b.type ORDER BY b.build_started_at ASC) 
            -- For non-pull_request types, get the max revision for each pull_request
            ELSE (
                SELECT MAX(revision) 
                FROM (
                    SELECT 
                        pull_request, 
                        ROW_NUMBER() OVER(PARTITION BY pull_request ORDER BY build_started_at ASC) AS revision
                    FROM builds AS sub_b
                    WHERE sub_b.pull_request = b.pull_request AND sub_b.type = 'pull_request'
                ) 
            )
        END AS revision,
        JULIANDAY(MAX(b.build_started_at) OVER(PARTITION BY b.pull_request)) - JULIANDAY(MIN(b.build_started_at) OVER(PARTITION BY b.pull_request)) AS raw_duration_in_days,
        MAX(CASE WHEN b.type = 'commit' THEN 1 ELSE 0 END) OVER(PARTITION BY b.pull_request) AS has_commit, 
        CASE WHEN author = 'nan' 
            THEN SUBSTR(label, 0, INSTR(label, ':')) 
            ELSE author 
        END AS author,
        CASE
            WHEN type = 'commit' THEN 'nanocurrency'
            ELSE SUBSTR(label, 0, INSTR(label, ':'))
        END AS commit_user
        ,*
    FROM 
        builds b    
    WHERE b.build_started_at != 'None'
    --AND b.pull_request != 'None'
)
SELECT 
    hash,
    pull_request,
    build_started_at,
    CASE 
        WHEN JULIANDAY(date('now')) - JULIANDAY(build_started_at) < 0 THEN 'today'
        WHEN JULIANDAY(date('now')) - JULIANDAY(build_started_at) < 1 THEN 'yesterday'
        ELSE CAST(ROUND(JULIANDAY(date('now')) - JULIANDAY(build_started_at)) +1 AS INTEGER) || ' day(s) ago'
    END AS last_modified,
    hash,
    CASE 
        WHEN type = 'pull_request' THEN 'pull request'        
        ELSE type
    END AS type,
    revision,
    CASE 
        WHEN has_commit > 0 THEN 
            CASE 
                WHEN type = 'commit' THEN 
                    CASE 
                        WHEN raw_duration_in_days < 1 THEN '< 1 day'
                        ELSE CAST(ROUND(raw_duration_in_days) AS INTEGER) || ' days' -- Cast the rounded value to INTEGER
                    END
                ELSE '0'
            END
        ELSE 
            CASE 
                WHEN JULIANDAY(date('now')) - JULIANDAY(MIN(build_started_at) OVER(PARTITION BY pull_request)) < 2 THEN '> 1 day'
                ELSE '> ' || CAST(ROUND(JULIANDAY(date('now')) - JULIANDAY(MIN(build_started_at) OVER(PARTITION BY pull_request))) AS INTEGER) || ' days' -- Cast the rounded value to INTEGER
            END
    END AS duration_in_days,
    CASE 
        WHEN has_commit > 0 THEN 'Yes'
        ELSE 'No'
    END AS matching_commit,
    testcase_run_id,
    build_run_id,
    CASE 
        WHEN overall_status = 'PASS' THEN '✅'
        WHEN overall_status = 'running' THEN '⌛'
        ELSE '❌'
    END AS overall_status,
    title,
    label, 
    author,
    'https://github.com/nanocurrency/nano-node/pull/' || pull_request AS pr_url,
    'https://github.com/gr0vity-dev/nano-node-builder/actions/runs/' || testcase_run_id AS testcase_url, 
    'https://github.com/gr0vity-dev/nano-node-builder/actions/runs/' || build_run_id AS build_url, 
    'https://github.com/' || SUBSTR(label, 0, INSTR(label, ':')) || '/nano-node/commits/' || SUBSTR(label, INSTR(label, ':') + 1) || '/' AS branch,    
    'https://github.com/' || commit_user || '/nano-node/commit/' || hash AS commit_url,
    'https://github.com/' || author || '.png?size=40' AS avatar
FROM CTE
{where_clause}
ORDER BY 
    build_started_at DESC;
"""
median_testcase_duration = """
WITH DurationData AS (
    SELECT 
        testcase,
        ROUND((julianday(completed_at) - julianday(started_at)) * 86400) AS duration
    FROM testcases
    WHERE sql_id IN (
        SELECT link_sql_id
        FROM mappings
        WHERE main_sql_id IN (
            SELECT sql_id
            FROM builds
            WHERE type = 'commit'
              AND build_started_at != 'None'
            ORDER BY build_started_at DESC
            LIMIT {count}
        )
    )
),
RankedDurations AS (
    SELECT 
        testcase,
        duration,
        ROW_NUMBER() OVER (PARTITION BY testcase ORDER BY duration) AS rn_asc,
        COUNT(*) OVER (PARTITION BY testcase) AS total
    FROM DurationData
)

SELECT 
    testcase,
    AVG(duration) AS average_duration,
    MAX(duration) AS max_duration,
    MIN(duration) AS min_duration,
    AVG(duration) FILTER (WHERE rn_asc IN (total / 2 + 1, (total + 1) / 2)) AS median_duration
FROM RankedDurations
GROUP BY testcase
"""


def format_median_testduration_query(count):
    query = median_testcase_duration.format(count=count)
    return query


def format_testcase_query(hash_value):
    query = base_testcase_query.format(hash_value=hash_value)
    return query


def format_query(hash_value=None, pull_request=None):
    conditions = []

    # Append conditions if values are provided
    if hash_value:
        conditions.append(f"hash = '{hash_value}'")
    if pull_request:
        conditions.append(f"pull_request = '{pull_request}'")

    # Form the WHERE clause based on the conditions
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    else:
        where_clause = ""

    query = base_query_template.format(where_clause=where_clause)
    return query
