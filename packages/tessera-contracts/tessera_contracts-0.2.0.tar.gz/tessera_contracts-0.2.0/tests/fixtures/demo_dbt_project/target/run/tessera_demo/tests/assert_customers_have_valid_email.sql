
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: ensure all customers have valid email format

select
    customer_id,
    email
from "demo"."main"."dim_customers"
where email not like '%@%.%'
  
  
      
    ) dbt_internal_test