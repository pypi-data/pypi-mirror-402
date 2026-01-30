





with validation_errors as (

    select
        date, channel
    from "memory"."main"."int_channel_daily"
    group by date, channel
    having count(*) > 1

)

select *
from validation_errors


