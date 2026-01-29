#!/usr/bin/env python3
"""
Base class for scheduling constraints.

Constraints are added to the problem before optimization and define
the feasibility requirements for valid schedules.
"""

from abc import ABC, abstractmethod


class ConstraintBase(ABC):
    """
    Abstract base class for scheduling constraints.

    Each constraint has:
    - A name for logging/debugging
    - An apply() method that adds constraints to the LP problem
    """

    def __init__(self, name: str):
        """
        Initialize a constraint.

        Args:
            name: Human-readable name for this constraint
        """
        self.name = name

    @abstractmethod
    def apply(self, scheduler) -> int:
        """
        Apply this constraint to the scheduler's LP problem.

        Args:
            scheduler: InstructorScheduler instance with problem setup
                      Has access to:
                      - scheduler.prob: The LpProblem to add constraints to
                      - scheduler.x: decision variables dict
                      - scheduler.keys: set of (course, room, time_slot) tuples
                      - scheduler.courses_df, rooms_df, time_slots_df: input data
                      - scheduler.enrollments, capacities, etc.: derived dicts

        Returns:
            Number of constraints added to the problem
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
