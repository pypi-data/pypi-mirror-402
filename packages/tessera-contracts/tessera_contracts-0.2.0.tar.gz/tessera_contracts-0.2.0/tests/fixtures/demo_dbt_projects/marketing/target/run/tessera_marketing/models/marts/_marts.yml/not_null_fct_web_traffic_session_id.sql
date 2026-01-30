
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select session_id
from "memory"."main"."fct_web_traffic"
where session_id is null



  
  
      
    ) dbt_internal_test