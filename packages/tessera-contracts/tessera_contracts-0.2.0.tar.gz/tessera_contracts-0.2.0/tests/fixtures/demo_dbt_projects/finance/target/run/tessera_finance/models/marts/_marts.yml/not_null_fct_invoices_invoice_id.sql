
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select invoice_id
from "memory"."main"."fct_invoices"
where invoice_id is null



  
  
      
    ) dbt_internal_test