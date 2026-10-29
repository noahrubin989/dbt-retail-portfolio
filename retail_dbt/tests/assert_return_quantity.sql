select *
from {{ ref('int_returns_signed') }}
where quantity >= 0