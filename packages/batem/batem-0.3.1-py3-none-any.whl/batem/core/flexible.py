"""Flexible geometry solver for BATEM building footprints.

.. module:: batem.flexible

This module provides a constraint-based geometry solver backed by Z3. It derives
consistent building dimensions and envelope areas from a minimal set of inputs
such as total floor area, floor height, and glazing ratios.

:Author: stephane.ploix@grenoble-inp.fr
:License: GNU General Public License v3.0
"""
from dataclasses import dataclass
from z3.z3 import ArithRef, CheckSatResult, ModelRef
from math import sqrt


try:
    from z3 import Real, Int, Solver, sat
except ImportError as exc:
    try:
        from z3.z3 import Real, Int, Solver, sat
    except ImportError:
        raise ImportError(
            "z3 symbols not found. Install the correct package: pip install z3-solver"
        ) from exc
from enum import Enum


class SIDE(Enum):
    """Cardinal facade labels used for glazing ratios."""

    MAIN = "main"
    RIGHT = "right"
    OPPOSITE = "opposite"
    LEFT = "left"


class GlazingRatios:
    """Container for glazing ratios per facade side."""

    def __init__(self, main: float = 0, right: float = 0, opposite: float = 0, left: float = 0):
        """Initialize glazing ratios.

        :param main: Glazing ratio for the main facade.
        :type main: float
        :param right: Glazing ratio for the right facade.
        :type right: float
        :param opposite: Glazing ratio for the opposite facade.
        :type opposite: float
        :param left: Glazing ratio for the left facade.
        :type left: float
        """
        self._ratio_glazing: dict[str, float] = {SIDE.MAIN.value: main, SIDE.RIGHT.value: right, SIDE.OPPOSITE.value: opposite, SIDE.LEFT.value: left}

    def __call__(self, side: SIDE | None = None) -> dict[str, float] | str:
        """Return glazing ratios or a single side ratio.

        :param side: Facade side to retrieve. If ``None``, returns all sides.
        :type side: SIDE | None
        :return: Glazing ratio(s) for the requested side(s).
        :rtype: dict[str, float] | str
        :raises ValueError: If any ratio is unset when requesting all sides.
        """
        if side is None:
            for side in self._ratio_glazing:
                if self._ratio_glazing[side] is None:
                    raise ValueError(f"Ratio glazing for {side} is not set")
            return self._ratio_glazing
        else:
            return self._ratio_glazing[side.value]

    def set_all(self, value: float) -> None:
        """Set the same glazing ratio for all facades.

        :param value: Glazing ratio to apply to all sides.
        :type value: float
        :return: ``self`` for fluent chaining.
        :rtype: GlazingRatios
        """
        for key in self._ratio_glazing:
            self._ratio_glazing[key] = value
        return self

    def set_side(self, side: SIDE, value: float) -> None:
        """Set the glazing ratio for a specific facade side.

        :param side: Facade side to update.
        :type side: SIDE
        :param value: Glazing ratio to apply.
        :type value: float
        :return: ``self`` for fluent chaining.
        :rtype: GlazingRatios
        """
        self._ratio_glazing[side.value] = value
        return self

    def __repr__(self) -> str:
        return f"Ratio glazing: {SIDE.MAIN.value}: {self._ratio_glazing[SIDE.MAIN.value]}, {SIDE.RIGHT.value}: {self._ratio_glazing[SIDE.RIGHT.value]}, {SIDE.OPPOSITE.value}: {self._ratio_glazing[SIDE.OPPOSITE.value]}, {SIDE.LEFT.value}: {self._ratio_glazing[SIDE.LEFT.value]}"


@dataclass
class Geometry:
    """Resolved geometry and envelope metrics for a flexible building."""

    floor_height: float
    n_floors: float
    building_width: float
    building_depth: float
    building_height: float
    S_floor: float
    S_glazing_main: float
    S_glazing_right: float
    S_glazing_opposite: float
    S_glazing_left: float
    S_glazing_main_per_floor: float
    S_glazing_right_per_floor: float
    S_glazing_opposite_per_floor: float
    S_glazing_left_per_floor: float
    S_glazing_total: float
    S_wall: float
    window_heights: list[float]
    air_volume: float


class FlexibleBuilding:
    """Constraint-based solver for building geometry and envelope areas."""

    def __init__(self, S_floor_total: float, floor_height: float, glazing_ratios: GlazingRatios, n_floors: int = 1, shape_factor: float = 1.0, keep_glazing_total: bool = True):
        """Initialize the flexible building: it can yield different geometries related to different glazing ratios, number of floors and shape factors but whatever the variant it is, the total floor surface, and floor height are same.

        :param S_floor_total: Total floor area across all floors.
        :type S_floor_total: float
        :param floor_height: Height per floor.
        :type floor_height: float
        :param glazing_ratios_ref: Reference glazing ratios.
        :type glazing_ratios_ref: GlazingRatios
        :param n_floors_ref: Reference number of floors.
        :type n_floors_ref: int
        :param shape_factor_ref: Reference shape factor (width/depth ratio).
        :type shape_factor_ref: float
        :param keep_glazing_total: If True, keeps total glazing surface constant.
        :type keep_glazing_total: bool
        """
        # Invariants
        self.glazing_ratios_ref: GlazingRatios = glazing_ratios
        self.n_floors_ref: int = n_floors
        self.shape_factor_ref: float = shape_factor
        self.S_floor_total_ref: float = S_floor_total
        self.floor_height_ref: float = floor_height
        self.keep_glazing_total: bool = keep_glazing_total

        # flexible variables
        self.n_floors: ArithRef = Int("n_floors")
        self.shape_factor: ArithRef = Real("shape_factor")
        self.glazing_ratio_correction: ArithRef = Real("glazing_ratio_correction")
        # self.glazing_ratio_correction: float = 1
        self.building_width: ArithRef = Real("building_width")
        self.building_depth: ArithRef = Real("building_depth")
        self.building_height: ArithRef = Real("building_height")
        self.S_floor: ArithRef = Real("S_floor")

        # main side
        self.ratio_glazing_main: ArithRef = Real("ratio_glazing_main")
        self.S_glazing_main: ArithRef = Real("S_glazing_main")

        # right side
        self.S_glazing_right: ArithRef = Real("S_glazing_right")
        self.ratio_glazing_right: ArithRef = Real("ratio_glazing_right")
        # opposite side
        self.ratio_glazing_opposite: ArithRef = Real("ratio_glazing_opposite")
        self.S_glazing_opposite: ArithRef = Real("S_glazing_opposite")
        # left side
        self.ratio_glazing_left: ArithRef = Real("ratio_glazing_left")
        self.S_glazing_left: ArithRef = Real("S_glazing_left")
        
        self.S_glazing_total: ArithRef = Real("S_glazing_total")
        self.S_main: ArithRef = Real("S_main")
        self.S_right: ArithRef = Real("S_right")
        self.S_opposite: ArithRef = Real("S_opposite")
        self.S_left: ArithRef = Real("S_left")

        self.building_width_ref = sqrt(self.S_floor_total_ref*self.shape_factor_ref)
        self.building_depth_ref = sqrt(self.S_floor_total_ref/self.shape_factor_ref)
        self.main_side_surface_ref = self.building_width_ref * self.floor_height_ref * self.n_floors_ref
        self.lr_side_surface_ref = self.building_depth_ref * self.floor_height_ref * self.n_floors_ref
        self.S_glazing_total_ref = self.main_side_surface_ref*self.glazing_ratios_ref(SIDE.MAIN) + self.lr_side_surface_ref*self.glazing_ratios_ref(SIDE.RIGHT) + self.main_side_surface_ref*self.glazing_ratios_ref(SIDE.OPPOSITE) + self.lr_side_surface_ref*self.glazing_ratios_ref(SIDE.LEFT)
        # Build solver
        self.solver: Solver = Solver()

        # Invariant constraints (nonlinear polynomial constraints over reals)
        self.solver.add(
            self.S_floor_total_ref == self.S_floor * self.n_floors,
            self.S_floor == self.building_width * self.building_depth,
            self.building_height == self.n_floors * self.floor_height_ref,
            self.building_width**2 == self.S_floor * self.shape_factor,
            self.building_depth**2 == self.S_floor / self.shape_factor,
            self.S_main == self.building_width * self.floor_height_ref * self.n_floors,
            self.S_right == self.building_depth * self.floor_height_ref * self.n_floors,
            self.S_opposite == self.building_width * self.floor_height_ref * self.n_floors,
            self.S_left == self.building_depth * self.floor_height_ref * self.n_floors,
            self.S_glazing_main == self.S_main * self.ratio_glazing_main * self.glazing_ratio_correction,
            self.S_glazing_right == self.S_right * self.ratio_glazing_right * self.glazing_ratio_correction,
            self.S_glazing_opposite == self.S_opposite * self.ratio_glazing_opposite * self.glazing_ratio_correction,
            self.S_glazing_left == self.S_left * self.ratio_glazing_left * self.glazing_ratio_correction,
            self.S_glazing_total == self.S_glazing_main + self.S_glazing_right + self.S_glazing_opposite + self.S_glazing_left,
            self.n_floors > 0,
            self.shape_factor > 0,
            self.glazing_ratio_correction > 0,
            self.building_depth > 0,
            self.building_width > 0,
            self.building_height > 0,
            self.S_floor > 0,
            self.S_glazing_main > 0,
            self.S_glazing_right > 0,
            self.S_glazing_opposite > 0,
            self.S_glazing_left > 0,
            self.S_main > 0,
            self.S_right > 0,
            self.S_opposite > 0,
            self.S_left > 0,
        )
        if self.keep_glazing_total:
            self.solver.add(self.S_glazing_total == self.S_glazing_total_ref)
        else:
            self.solver.add(self.glazing_ratio_correction == 1.0)

    def solve(self, n_floors: int = 1, shape_factor: float = 1, glazing_ratios: GlazingRatios | None = None) -> Geometry | None:
        """Solve the constraint system and return resolved geometry.

        :param n_floors: Number of floors to solve for.
        :type n_floors: int
        :param shape_factor: Shape factor (width/depth ratio).
        :type shape_factor: float
        :param glazing_ratios: Optional glazing ratios override.
        :type glazing_ratios: GlazingRatios | None
        :return: Resolved geometry or ``None`` if unsatisfiable.
        :rtype: Geometry | None
        """
        try:
            self.solver.pop()
        except Exception:
            pass
        self.solver.push()
        self.solver.add(
            self.n_floors == n_floors,
            self.shape_factor == shape_factor,
        )
        if glazing_ratios is None:
            glazing_ratios = self.glazing_ratios_ref
        if glazing_ratios is not None:
            self.solver.add(
                self.ratio_glazing_main == glazing_ratios(SIDE.MAIN),
                self.ratio_glazing_right == glazing_ratios(SIDE.RIGHT),
                self.ratio_glazing_opposite == glazing_ratios(SIDE.OPPOSITE),
                self.ratio_glazing_left == glazing_ratios(SIDE.LEFT),
            )
        status: CheckSatResult = self.solver.check()

        if status == sat:
            model: ModelRef = self.solver.model()
        else:
            print("No solution: missing or inconsistent data")
            self.solver.pop()
            return None
        
        self.solver.pop()
        building_width: float = self._eval(model, self.building_width)
        building_depth: float = self._eval(model, self.building_depth)
        building_height: float = self._eval(model, self.building_height)
        S_floor: float = self._eval(model, self.S_floor)
        S_glazing_main: float = self._eval(model, self.S_glazing_main)
        S_glazing_right: float = self._eval(model, self.S_glazing_right)
        S_glazing_opposite: float = self._eval(model, self.S_glazing_opposite)
        S_glazing_left: float = self._eval(model, self.S_glazing_left)
        S_glazing_main_per_floor: float = S_glazing_main / n_floors
        S_glazing_right_per_floor: float = S_glazing_right / n_floors
        S_glazing_opposite_per_floor: float = S_glazing_opposite / n_floors
        S_glazing_left_per_floor: float = S_glazing_left / n_floors
        
        S_glazing_total: float = S_glazing_main + S_glazing_right + S_glazing_opposite + S_glazing_left
        S_main: float = self._eval(model, self.S_main)
        S_right: float = self._eval(model, self.S_right)
        S_opposite: float = self._eval(model, self.S_opposite)
        S_left: float = self._eval(model, self.S_left)
        S_wall: float = S_main + S_right + S_opposite + S_left - S_glazing_total
        window_heights: list[float] = [building_height * (i+0.5) / n_floors for i in range(n_floors)]
        air_volume: float = building_width * building_depth * building_height
        return Geometry(
            self.floor_height_ref,
            n_floors,
            building_width,
            building_depth,
            building_height,
            S_floor,
            S_glazing_main,
            S_glazing_right,
            S_glazing_opposite,
            S_glazing_left,
            S_glazing_main_per_floor,
            S_glazing_right_per_floor,
            S_glazing_opposite_per_floor,
            S_glazing_left_per_floor,
            S_glazing_total,
            S_wall,
            window_heights,
            air_volume,
        )

    @staticmethod
    def _eval(model, expr: ArithRef) -> float:
        """Evaluate a Z3 expression to a float.

        :param model: Z3 model holding the solution.
        :type model: ModelRef
        :param expr: Z3 arithmetic expression to evaluate.
        :type expr: ArithRef
        :return: Numeric value for the expression.
        :rtype: float
        """
        value = model.eval(expr, model_completion=True)
        if value.is_int():
            return float(value.as_long())
        return float(value.as_decimal(12).replace("?", ""))


if __name__ == "__main__":
    glazing_ratios: GlazingRatios = GlazingRatios()
    building: FlexibleBuilding = FlexibleBuilding(S_floor_total=100, floor_height=3, glazing_ratios=glazing_ratios.set_all(0.1), n_floors=1, shape_factor=1.0)
    geometry: Geometry = building.solve()
    print('Initial geometry:')
    print(geometry)
    # print("===> Total glazing surface: %f m2" % geometry.S_glazing_total)
    geometry: Geometry = building.solve(n_floors=2, shape_factor=1, glazing_ratios=glazing_ratios.set_all(0.1))
    print('Second geometry:')
    print(geometry)
    # print("===> Total glazing surface: %f m2" % geometry.S_glazing_total)
    # glazing_ratios.set_side(SIDE.MAIN, .3)
    # glazing_ratios.set_side(SIDE.RIGHT, .5)
    # geometry: Geometry = building.solve(n_floors=2, shape_factor=1, glazing_ratios=glazing_ratios)
    # print('Second geometry:')
    # print(geometry)
    # geometry: Geometry = building.solve(n_floors=3, shape_factor=2, glazing_ratios=glazing_ratios)
    # print('Third geometry:')
    # print(geometry)