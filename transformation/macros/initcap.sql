{# Title-case each whitespace-separated word (e.g. countries, places) #}
{% macro initcap(field_name) -%}
    case
        when {{ field_name }} is null then null
        when trim(cast({{ field_name }} as varchar)) = '' then null
        else (
            [
                upper(word[1]) || word[2:]
                for word in string_split(lower(trim(cast({{ field_name }} as varchar))), ' ')
                if word != ''
            ]
        ).list_aggr('string_agg', ' ')
    end
{%- endmacro %}
