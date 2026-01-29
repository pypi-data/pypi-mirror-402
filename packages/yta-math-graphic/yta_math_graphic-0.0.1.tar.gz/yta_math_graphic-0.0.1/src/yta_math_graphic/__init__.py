"""
Module to include the functionality related
to easings.

Thanks for the inspiration:
- https://github.com/semitable/easing-functions/blob/master/easing_functions
"""
from yta_math_easings.linear import LinearEasing
from yta_math_easings.slow_into import SlowIntoEasing
from yta_math_easings.smooth import SmoothEasing
from yta_math_easings.smooth_step import SmoothStepEasing
from yta_math_easings.smoother_step import SmootherStepEasing
from yta_math_easings.smootherer_step import SmoothererStepEasing

# TODO: Add more from 'yta_math.rate_functions'

"""
Here you have a list including the 'overshoot' of
the different easing functions, including also the
[X] sign for those that have been already included
in the library.

[X] linear - no
[X] smooth — no
[X] smooth_step — no
[X] smoother_step — no
[X] smootherer_step — no
[ ] rush_into — no
[ ] rush_from — no
[ ] double_smooth — no
[ ] there_and_back — no
[ ] there_and_back_with_pause — no
[ ] wiggle — sí
[ ] ease_in_cubic — no
[ ] ease_out_cubic — no
[ ] ease_in_out_cubic — no
[ ] ease_in_quad — no
[ ] ease_out_quad — no
[ ] ease_in_out_quad — no
[ ] ease_in_quart — no
[ ] ease_out_quart — no
[ ] ease_in_out_quart — no
[ ] ease_in_quint — no
[ ] ease_out_quint — no
[ ] ease_in_out_quint — no
[ ] ease_in_expo — no
[ ] ease_out_expo — no
[ ] ease_in_out_expo — no
[ ] ease_in_sine — no
[ ] ease_out_sine — no
[ ] ease_in_out_sine — no
[ ] ease_in_circ — no
[ ] ease_out_circ — no
[ ] ease_in_out_circ — no
[ ] ease_in_back — sí
[ ] ease_out_back — sí
[ ] ease_in_out_back — sí
[ ] ease_in_elastic — sí
[ ] ease_out_elastic — sí
[ ] ease_in_out_elastic — sí
[ ] ease_in_bounce — no
[ ] ease_out_bounce — no
[ ] ease_in_out_bounce — no
[ ] squish_rate_func — sí (depende de func)
[ ] lingering — no
[ ] exponential_decay — no
"""


__all__ = [
    'LinearEasing',
    'SlowIntoEasing',
    'SmoothEasing',
    'SmoothStepEasing',
    'SmootherStepEasing',
    'SmoothererStepEasing'
]


