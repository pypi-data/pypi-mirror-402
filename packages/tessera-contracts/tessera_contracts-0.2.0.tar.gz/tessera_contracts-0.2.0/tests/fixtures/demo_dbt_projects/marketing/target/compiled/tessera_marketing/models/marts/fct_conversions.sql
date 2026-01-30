with conversions as (
    select * from "memory"."main"."stg_conversions"
),

campaigns as (
    select campaign_id, channel, campaign_name from "memory"."main"."stg_campaigns"
)

select
    cv.conversion_id,
    cv.campaign_id,
    c.campaign_name,
    c.channel,
    cv.customer_id,
    cv.conversion_date,
    cv.conversion_type,
    cv.revenue,
    cv.is_revenue_generating,
    current_timestamp as _updated_at
from conversions cv
left join campaigns c on cv.campaign_id = c.campaign_id