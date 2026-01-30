
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select session_id
from "memory"."main"."stg_website_sessions"
where session_id is null



  
  
      
    ) dbt_internal_test