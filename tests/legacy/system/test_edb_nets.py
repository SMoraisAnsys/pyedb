"""Tests related to Edb nets
"""

import os
import pytest
from pyedb import Edb
from tests.conftest import desktop_version
from tests.conftest import local_path
from tests.legacy.system.conftest import test_subfolder

pytestmark = [pytest.mark.system, pytest.mark.legacy]

class TestClass:
    @pytest.fixture(autouse=True)
    def init(self, edbapp, local_scratch, target_path, target_path2, target_path4):
        self.edbapp = edbapp
        self.local_scratch = local_scratch
        self.target_path = target_path
        self.target_path2 = target_path2
        self.target_path4 = target_path4


    def test_nets_queries(self):
        """Evaluate nets queries"""
        assert len(self.edbapp.nets.netlist) > 0
        signalnets = self.edbapp.nets.signal
        assert not signalnets[list(signalnets.keys())[0]].is_power_ground
        assert not signalnets[list(signalnets.keys())[0]].IsPowerGround()
        assert len(list(signalnets[list(signalnets.keys())[0]].primitives)) > 0
        assert len(signalnets) > 2

        powernets = self.edbapp.nets.power
        assert len(powernets) > 2
        assert powernets["AVCC_1V3"].is_power_ground
        powernets["AVCC_1V3"].is_power_ground = False
        assert not powernets["AVCC_1V3"].is_power_ground
        powernets["AVCC_1V3"].is_power_ground = True
        assert powernets["AVCC_1V3"].name == "AVCC_1V3"
        assert powernets["AVCC_1V3"].IsPowerGround()
        assert len(list(powernets["AVCC_1V3"].components.keys())) > 0
        assert len(powernets["AVCC_1V3"].primitives) > 0

        assert self.edbapp.nets.find_or_create_net("GND")
        assert self.edbapp.nets.find_or_create_net(start_with="gn")
        assert self.edbapp.nets.find_or_create_net(start_with="g", end_with="d")
        assert self.edbapp.nets.find_or_create_net(end_with="d")
        assert self.edbapp.nets.find_or_create_net(contain="usb")
        assert self.edbapp.nets["AVCC_1V3"].extended_net is None
        self.edbapp.extended_nets.auto_identify_power()
        assert self.edbapp.nets["AVCC_1V3"].extended_net

    def test_nets_get_power_tree(self):
        """Evaluate nets get powertree."""
        OUTPUT_NET = "5V"
        GROUND_NETS = ["GND", "PGND"]
        (
            component_list,
            component_list_columns,
            net_group,
        ) = self.edbapp.nets.get_powertree(OUTPUT_NET, GROUND_NETS)
        assert component_list
        assert component_list_columns
        assert net_group

    def test_nets_delete(self):
        """Delete a net."""
        assert "JTAG_TDI" in self.edbapp.nets
        self.edbapp.nets["JTAG_TCK"].delete()
        nets_deleted = self.edbapp.nets.delete("JTAG_TDI")
        assert "JTAG_TDI" in nets_deleted
        assert "JTAG_TDI" not in self.edbapp.nets

    def test_nets_classify_nets(self):
        """Reassign power based on list of nets."""
        assert self.edbapp.nets.classify_nets(["RSVD_0", "RSVD_1"], ["V3P3_S0"])
        assert "RSVD_0" in self.edbapp.nets.power
        assert "RSVD_0" not in self.edbapp.nets.signal
        assert "RSVD_1" in self.edbapp.nets.power
        assert "RSVD_1" not in self.edbapp.nets.signal
        assert "V3P3_S0" not in self.edapp.nets.power
        assert "V3P3_S0" in self.edapp.nets.signal

    def test_arc_data(self):
        """Evaluate primitive arc data."""
        assert len(self.edbapp.nets["1.2V_DVDDL"].primitives[0].arcs) > 0
        assert self.edbapp.nets["1.2V_DVDDL"].primitives[0].arcs[0].start
        assert self.edbapp.nets["1.2V_DVDDL"].primitives[0].arcs[0].end
        assert self.edbapp.nets["1.2V_DVDDL"].primitives[0].arcs[0].height

    def test_dc_shorts(self):
        source_path = os.path.join(local_path, "example_models", test_subfolder, "ANSYS-HSD_V1.aedb")
        target_path = os.path.join(self.local_scratch.path, "test_dc_shorts", "ANSYS-HSD_V1_dc_shorts.aedb")
        self.local_scratch.copyfolder(source_path, target_path)
        edbapp = Edb(target_path, edbversion=desktop_version)
        dc_shorts = edbapp.layout_validation.dc_shorts()
        assert dc_shorts
        edbapp.nets.nets["DDR4_A0"].name = "DDR4$A0"
        edbapp.layout_validation.illegal_net_names(True)

        # assert len(dc_shorts) == 20
        assert ["LVDS_CH09_N", "GND"] in dc_shorts
        assert ["LVDS_CH09_N", "DDR4_DM3"] in dc_shorts
        assert ["DDR4_DM3", "LVDS_CH07_N"] in dc_shorts
        assert len(edbapp.nets["DDR4_DM3"].find_dc_short()) > 0
        edbapp.nets["DDR4_DM3"].find_dc_short(True)
        assert len(edbapp.nets["DDR4_DM3"].find_dc_short()) == 0
        edbapp.close()
