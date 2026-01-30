
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select channel
from "memory"."main"."stg_campaigns"
where channel is null



  
  
      
    ) dbt_internal_test