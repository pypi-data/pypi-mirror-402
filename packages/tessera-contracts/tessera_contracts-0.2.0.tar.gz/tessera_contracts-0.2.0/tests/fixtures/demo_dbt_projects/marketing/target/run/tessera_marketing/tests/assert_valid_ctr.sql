
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: CTR should be between 0 and 100%
select
    date,
    channel,
    ctr
from "memory"."main"."fct_marketing_daily"
where ctr < 0 or ctr > 1
  
  
      
    ) dbt_internal_test