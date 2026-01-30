
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_spend
from "memory"."main"."int_campaign_performance"
where total_spend is null



  
  
      
    ) dbt_internal_test