
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select pages_viewed
from "memory"."main"."fct_web_traffic"
where pages_viewed is null



  
  
      
    ) dbt_internal_test