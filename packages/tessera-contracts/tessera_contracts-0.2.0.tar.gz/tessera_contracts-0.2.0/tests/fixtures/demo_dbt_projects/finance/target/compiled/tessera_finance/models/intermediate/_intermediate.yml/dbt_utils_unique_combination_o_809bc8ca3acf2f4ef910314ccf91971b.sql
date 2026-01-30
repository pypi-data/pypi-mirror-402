





with validation_errors as (

    select
        month, category, subcategory
    from "memory"."main"."int_expense_by_category"
    group by month, category, subcategory
    having count(*) > 1

)

select *
from validation_errors


