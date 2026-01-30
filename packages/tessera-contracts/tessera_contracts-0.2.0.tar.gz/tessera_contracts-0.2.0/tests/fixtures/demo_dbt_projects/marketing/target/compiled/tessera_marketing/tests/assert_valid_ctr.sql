-- Singular test: CTR should be between 0 and 100%
select
    date,
    channel,
    ctr
from "memory"."main"."fct_marketing_daily"
where ctr < 0 or ctr > 1