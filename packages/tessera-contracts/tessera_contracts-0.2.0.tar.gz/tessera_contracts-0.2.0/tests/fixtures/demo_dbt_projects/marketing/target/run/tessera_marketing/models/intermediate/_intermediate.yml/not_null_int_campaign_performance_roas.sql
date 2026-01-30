
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select roas
from "memory"."main"."int_campaign_performance"
where roas is null



  
  
      
    ) dbt_internal_test