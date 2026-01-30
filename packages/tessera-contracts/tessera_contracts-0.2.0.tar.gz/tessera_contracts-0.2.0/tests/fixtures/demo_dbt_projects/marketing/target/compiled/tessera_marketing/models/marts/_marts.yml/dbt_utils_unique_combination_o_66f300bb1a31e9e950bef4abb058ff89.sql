





with validation_errors as (

    select
        date, channel
    from "memory"."main"."fct_marketing_daily"
    group by date, channel
    having count(*) > 1

)

select *
from validation_errors


