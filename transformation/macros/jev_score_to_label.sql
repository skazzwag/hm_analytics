{# Map a Jev rubric score to its criterion label.
   The score is a weighted position on the 0-3 rubric (0 = first criterion,
   3 = last); round it to the nearest criterion index. DuckDB lists are
   1-indexed, so offset the rounded score by 1. DuckDB round() is
   half-away-from-zero, so exact .5 ties select the higher criterion
   (e.g. 2.5 -> 'Extreme'). #}
{% macro jev_score_to_label(criteria, score) -%}
    {{ criteria }}[round({{ score }}) + 1]
{%- endmacro %}
