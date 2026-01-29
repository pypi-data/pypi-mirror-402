# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from typing import Literal

from pydantic import PrivateAttr

from .common import (
    Experiment,
)


class ProcessTomography(Experiment):
    """
    Parameters for running quantum process tomography experiment.

    This experiment characterizes an unknown quantum operation by preparing
    a tomographically complete set of input states, applying the specified gate,
    and measuring the resulting output states.

    Attributes
    ----------
    transmon : list[str]
        The qubits (transmons) involved in the process.
        Only two-qubit tomography is supported at this time.
    gate : str
        The name of the gate or operation to characterize.
    method : "direct" or "mle", optional
        The reconstruction method used to estimate the process matrix.
        "direct" performs linear inversion; "mle" performs maximum-likelihood estimation.
        Defaults to "direct".
    recycle_delay_ns : int
        The delay between consecutive shots, in nanoseconds. Defaults to 500,000 ns.
    shot_count : int, optional
        The number of shots to take. Defaults to 1000.
    update : "auto" or "off" or "prompt", optional
        How the device should be updated after an experiment run. Defaults to auto.
    """

    _experiment_name: str = PrivateAttr("process_tomography")

    transmon: list[str]
    gate: str
    method: Literal["direct", "mle"] = "direct"
    recycle_delay_ns: int = 500_000
    shot_count: int = 1000
    update: Literal["auto", "off", "prompt"] = "auto"
