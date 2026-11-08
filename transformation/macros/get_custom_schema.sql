{#
    Prod: custom schema is used as-is.
    Other environments: all models build in the target schema.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if node.fqn[1] == '6_access' and custom_schema_name is not none -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ generate_schema_name_for_env(custom_schema_name, node) }}
    {%- endif -%}
{%- endmacro %}
