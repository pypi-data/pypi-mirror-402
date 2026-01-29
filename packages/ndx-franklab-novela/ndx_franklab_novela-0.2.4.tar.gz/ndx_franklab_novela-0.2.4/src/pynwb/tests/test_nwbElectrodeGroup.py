import numpy as np
import unittest
from unittest.mock import Mock

from pynwb.device import Device

from ndx_franklab_novela import NwbElectrodeGroup


class TestNwbElectrodeGroup(unittest.TestCase):

    def test_nwb_electrode_group_successful_created(self):
        name = "NwbElectrodeGroup 1"
        description = "Sample description"
        location = "Sample location"
        device = Mock(spec=Device)
        position = [1, 2, 3]
        targeted_location = "mPFC"
        targeted_x = 1.0
        targeted_y = 2.0
        targeted_z = 3.0
        units = "um"

        nwb_electrode_group = NwbElectrodeGroup(
            name=name,
            description=description,
            location=location,
            device=device,
            position=position,
            targeted_location=targeted_location,
            targeted_x=targeted_x,
            targeted_y=targeted_y,
            targeted_z=targeted_z,
            units=units,
        )

        self.assertIsInstance(nwb_electrode_group, NwbElectrodeGroup)
        self.assertEqual(nwb_electrode_group.name, name)
        self.assertEqual(nwb_electrode_group.description, description)
        self.assertEqual(nwb_electrode_group.location, location)
        self.assertEqual(nwb_electrode_group.device, device)
        np.testing.assert_array_equal(
            nwb_electrode_group.position, np.array((1.0, 2.0, 3.0), dtype=[("x", "<f8"), ("y", "<f8"), ("z", "<f8")])
        )
        self.assertEqual(nwb_electrode_group.targeted_location, targeted_location)
        self.assertEqual(nwb_electrode_group.targeted_x, targeted_x)
        self.assertEqual(nwb_electrode_group.targeted_y, targeted_y)
        self.assertEqual(nwb_electrode_group.targeted_z, targeted_z)
        self.assertEqual(nwb_electrode_group.units, units)
