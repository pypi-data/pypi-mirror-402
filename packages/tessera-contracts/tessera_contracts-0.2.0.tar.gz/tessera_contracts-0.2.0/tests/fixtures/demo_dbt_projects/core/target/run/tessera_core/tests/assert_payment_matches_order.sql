
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: ensure payments match order amounts (within 20% tolerance for demo data)
-- In production, this tolerance would be much stricter
select
    p.payment_id,
    p.order_id,
    p.amount as payment_amount,
    o.gross_amount as order_amount,
    abs(p.amount - o.gross_amount) as difference
from "memory"."main"."fct_payments" p
join "memory"."main"."fct_orders" o on p.order_id = o.order_id
where p.status = 'success'
  and o.gross_amount > 0
  and abs(p.amount - o.gross_amount) / o.gross_amount > 0.20
  
  
      
    ) dbt_internal_test