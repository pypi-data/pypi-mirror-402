
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    expense_id as unique_field,
    count(*) as n_records

from "memory"."main"."stg_expenses"
where expense_id is not null
group by expense_id
having count(*) > 1



  
  
      
    ) dbt_internal_test