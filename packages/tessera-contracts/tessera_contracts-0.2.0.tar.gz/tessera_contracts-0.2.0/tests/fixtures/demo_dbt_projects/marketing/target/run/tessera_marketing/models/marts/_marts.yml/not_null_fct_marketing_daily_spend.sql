
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select spend
from "memory"."main"."fct_marketing_daily"
where spend is null



  
  
      
    ) dbt_internal_test