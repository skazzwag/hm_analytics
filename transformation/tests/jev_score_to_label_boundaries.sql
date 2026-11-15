-- Singular test: boundary behavior of the jev_score_to_label macro on both
-- Jev scales, asserted against literals. Pure SQL (no AI functions), so it
-- runs on every target including dev-local duckdb. Fails when any row is
-- returned: 0 -> first label, 1.4 -> second, 2.5 -> last (round() is
-- half-away-from-zero, so exact .5 ties select the higher criterion),
-- 3 -> last.

with severity_checks as (
    select
        score_value,
        expected_label,
        {{ jev_score_to_label(['Mild', 'Moderate', 'High', 'Extreme'], 'score_value') }} as actual_label
    from (values
        (0.0, 'Mild'),
        (1.4, 'Moderate'),
        (2.5, 'Extreme'),
        (3.0, 'Extreme')
    ) severity_rows(score_value, expected_label)
),

frequency_checks as (
    select
        score_value,
        expected_label,
        {{ jev_score_to_label(['Isolated', 'Occasional', 'Frequent', 'Pervasive'], 'score_value') }} as actual_label
    from (values
        (0.0, 'Isolated'),
        (1.4, 'Occasional'),
        (2.5, 'Pervasive'),
        (3.0, 'Pervasive')
    ) frequency_rows(score_value, expected_label)
),

final as (
    select
        'severity' as scale,
        score_value,
        expected_label,
        actual_label
    from severity_checks
    where actual_label is distinct from expected_label

    union all

    select
        'frequency' as scale,
        score_value,
        expected_label,
        actual_label
    from frequency_checks
    where actual_label is distinct from expected_label
)

select
    scale,
    score_value,
    expected_label,
    actual_label
from final
