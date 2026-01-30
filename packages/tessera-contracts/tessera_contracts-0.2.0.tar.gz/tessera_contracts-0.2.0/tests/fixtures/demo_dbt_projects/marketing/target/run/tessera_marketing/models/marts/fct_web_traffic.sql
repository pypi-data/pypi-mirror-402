
  
  create view "memory"."main"."fct_web_traffic__dbt_tmp" as (
    with sessions as (
    select * from "memory"."main"."stg_website_sessions"
)

select
    session_id,
    visitor_id,
    session_date,
    source,
    medium,
    campaign_id,
    pages_viewed,
    session_duration_sec,
    session_duration_min,
    converted,
    case
        when session_duration_min >= 5 then 'engaged'
        when session_duration_min >= 1 then 'browsing'
        else 'bounce'
    end as engagement_level,
    current_timestamp as _updated_at
from sessions
  );
