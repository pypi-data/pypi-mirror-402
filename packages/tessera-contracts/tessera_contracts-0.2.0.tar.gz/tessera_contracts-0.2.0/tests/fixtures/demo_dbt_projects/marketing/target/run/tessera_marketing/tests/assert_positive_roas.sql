
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: completed campaigns should have positive ROAS
select
    campaign_id,
    campaign_name,
    roas
from "memory"."main"."dim_campaigns"
where status = 'completed'
  and roas < 0
  
  
      
    ) dbt_internal_test