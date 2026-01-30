
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select line_margin
from "memory"."main"."int_order_items_enriched"
where line_margin is null



  
  
      
    ) dbt_internal_test