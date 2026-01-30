
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: all invoices should have positive amounts
select
    invoice_id,
    amount
from "memory"."main"."fct_invoices"
where amount <= 0
  
  
      
    ) dbt_internal_test