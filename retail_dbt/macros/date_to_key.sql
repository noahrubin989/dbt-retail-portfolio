{% macro date_to_key(column_name) %}
    cast(strftime({{ column_name }}, '%Y%m%d') as integer)
{% endmacro %}
