
    
    

select
    expense_id as unique_field,
    count(*) as n_records

from "memory"."main"."stg_expenses"
where expense_id is not null
group by expense_id
having count(*) > 1


