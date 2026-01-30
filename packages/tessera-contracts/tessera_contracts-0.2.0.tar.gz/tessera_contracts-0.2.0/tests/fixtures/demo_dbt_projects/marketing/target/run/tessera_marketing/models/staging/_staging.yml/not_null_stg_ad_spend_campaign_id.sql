
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select campaign_id
from "memory"."main"."stg_ad_spend"
where campaign_id is null



  
  
      
    ) dbt_internal_test