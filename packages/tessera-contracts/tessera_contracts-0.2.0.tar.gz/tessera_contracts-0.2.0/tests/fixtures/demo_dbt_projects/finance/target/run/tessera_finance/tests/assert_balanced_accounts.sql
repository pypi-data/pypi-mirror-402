
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  -- Singular test: revenue and expense accounts should have parent
select
    account_id,
    account_name,
    account_type
from "memory"."main"."dim_accounts"
where account_type in ('revenue', 'expense')
  and parent_account_id is null
  and account_level > 0
  
  
      
    ) dbt_internal_test