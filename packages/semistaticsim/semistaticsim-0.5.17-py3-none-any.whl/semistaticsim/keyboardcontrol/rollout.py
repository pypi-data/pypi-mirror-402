from abc import ABC
from typing import List, Dict, Union, Self, Any

import flax
import numpy as np
from flax import struct

from semistaticsim.datawrangling.sssd import GeneratedSemiStaticData
from semistaticsim.keyboardcontrol.main_skillsim import ROBOTS
from semistaticsim.rendering.simulation.skill_simulator import Simulator

class Agent(ABC):
    def __init__(self, sim: Simulator):
        self.sim = sim

    @property
    def current_time(self):
        return self.sim.sss_data.pickupable_selves_at_current_time._timestamp[0]

    def _resolve_query_into_pickupable(self, query: str, current_time: float) -> List[str]:
        """

        Args:
            query: An open-vocab query specifying a target pickupable.

        Returns: The top N most likely pickupables, sorted by likelihood (most likely is at index 0)

        """
        raise NotImplementedError()

    def resolve_query_into_pickupable(self, query: str, current_time: float=None) -> List[str]:
        if current_time is None:
            current_time = self.current_time
        return self._resolve_query_into_pickupable(query, current_time)

    def _resolve_pickupable_into_weighted_receptacles(self, pickupable: str, current_time: float = None) -> Dict[str, float]:
        """

        Args:
            pickupable: A requested pickupable.
            current_time:

        Returns: A probability weight for each receptacle for the current location of the pickupable.

        """
        raise NotImplementedError()

    def resolve_pickupable_into_weighted_receptacles(self, pickupable: str, current_time: float=None) -> Dict[str, float]:
        if current_time is None:
            current_time = self.current_time

        return self._resolve_pickupable_into_weighted_receptacles(pickupable, current_time)

    def update(self, observation: Dict[str, Any]) -> Union[None, Self]:
        """

        Args:
            observation: An observation of the current state.

        Returns: A new Agent instance that has been updated given the observation.

        """
        raise NotImplementedError()

    def found_pickupable(self, pickupable_name: str, observation: Dict[str, Any]) -> bool:
        """

        Args:
            observation: An observation of the current state.

        Returns: True if the current state contains the pickupable, False otherwise.

        """
        raise NotImplementedError()

    def goto_query(self, query: str, current_time: float=None, custom_traversal=None) -> List[str]:
        pickupables = self.resolve_query_into_pickupable(query, current_time)

        pickupable = pickupables[0]
        weighted_receptacles = self.resolve_pickupable_into_weighted_receptacles(pickupable, current_time)
        sorted_keys = sorted(weighted_receptacles, key=weighted_receptacles.get, reverse=True)

        if custom_traversal is not None:
            return custom_traversal(sorted_keys)

        for k in sorted_keys:
            self.sim.GoToObject(ROBOTS[0], k, max_path_length=2)
            obs = self.sim.render()
            self.sim.privileged_apn = None

            if self.found_pickupable(pickupable, obs):
                return obs
            self.update(obs)
