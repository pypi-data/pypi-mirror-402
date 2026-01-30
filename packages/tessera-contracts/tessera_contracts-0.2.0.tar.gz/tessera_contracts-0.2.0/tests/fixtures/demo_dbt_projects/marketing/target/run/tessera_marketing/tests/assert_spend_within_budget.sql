
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: campaign spend should not exceed budget
select
    campaign_id,
    campaign_name,
    budget,
    total_spend,
    total_spend - budget as overspend
from "memory"."main"."dim_campaigns"
where total_spend > budget * 1.1  -- 10% tolerance
  
  
      
    ) dbt_internal_test