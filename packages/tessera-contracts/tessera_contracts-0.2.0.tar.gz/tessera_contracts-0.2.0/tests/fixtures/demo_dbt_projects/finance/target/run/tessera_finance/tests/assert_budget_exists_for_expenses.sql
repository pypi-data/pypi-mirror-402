
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: expenses should have corresponding budgets
-- Note: In demo data, some expense categories may not have budgets defined
select distinct
    e.category,
    e.expense_date
from "memory"."main"."fct_expenses" e
left join "memory"."main"."fct_budget_performance" b on e.category = b.category
where b.budgeted_amount is null
  and e.category not in ('hr')  -- HR expenses may span multiple budget periods
  
  
      
    ) dbt_internal_test