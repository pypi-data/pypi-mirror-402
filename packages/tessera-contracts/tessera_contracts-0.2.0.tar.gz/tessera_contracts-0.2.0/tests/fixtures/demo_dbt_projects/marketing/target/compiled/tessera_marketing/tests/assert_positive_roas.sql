-- Singular test: completed campaigns should have positive ROAS
select
    campaign_id,
    campaign_name,
    roas
from "memory"."main"."dim_campaigns"
where status = 'completed'
  and roas < 0