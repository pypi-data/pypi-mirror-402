
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    conversion_id as unique_field,
    count(*) as n_records

from "memory"."main"."fct_conversions"
where conversion_id is not null
group by conversion_id
having count(*) > 1



  
  
      
    ) dbt_internal_test