
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: products should have positive margin
select
    product_id,
    product_name,
    cost,
    list_price,
    margin
from "memory"."main"."dim_products"
where margin < 0
  and is_active = true
  
  
      
    ) dbt_internal_test