
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "memory"."main"."fct_invoices"
    group by status

)

select *
from all_values
where value_field not in (
    'pending','paid','overdue','cancelled'
)


