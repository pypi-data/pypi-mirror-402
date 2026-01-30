
    
    

select
    budget_id as unique_field,
    count(*) as n_records

from "memory"."main"."stg_budgets"
where budget_id is not null
group by budget_id
having count(*) > 1


