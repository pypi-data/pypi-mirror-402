from django.test import TestCase
from eveuniverse.models import EveType

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.tests.auth_utils import AuthUtils

from fleetcomp.models import FleetCommander, FleetMember, FleetSnapshot
from fleetcomp.tests.testdata.load_eveuniverse import load_eveuniverse


class TestSnapshot(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_eveuniverse()
        # create a global fleet commander
        cls.user = AuthUtils.create_user("test_user")
        cls.character = AuthUtils.add_main_character_2(
            cls.user, "test character", 1, "123", "Test corporation", "TEST"
        )
        character_ownership = CharacterOwnership.objects.create(
            character=cls.character,
            user=cls.user,
            owner_hash="fake hash",
        )
        cls.fleet_commander = FleetCommander.objects.create(
            character_ownership=character_ownership,
        )

        cls.revelation_type: EveType = EveType.objects.get(id=19720)
        cls.caracal_type: EveType = EveType.objects.get(id=621)

    def setUp(self):
        self.fleet_snapshot: FleetSnapshot = FleetSnapshot.objects.create(
            fleet_id=10,
            commander=self.fleet_commander,
        )

    def tearDown(self):
        self.fleet_snapshot.delete()

    def test_main_ship_reduce_dread(self):

        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.revelation_type,
        )
        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.revelation_type,
        )
        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.caracal_type,
        )

        self.assertEqual(self.fleet_snapshot.get_main_ship_type(), self.caracal_type)

    def test_calc_subcap_mass_without_caps(self):
        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.revelation_type,
        )

        self.assertEqual(self.fleet_snapshot.get_subcap_mass_tons(), 0)

    def test_calc_mass_with_cap_only(self):
        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.revelation_type,
        )

        self.assertEqual(
            self.fleet_snapshot.get_total_mass_tons(), self.revelation_type.mass / 1000
        )

    def test_calc_mass_with_subcaps_only(self):
        FleetMember.objects.create(
            fleet=self.fleet_snapshot,
            character=self.character,
            ship_type=self.caracal_type,
        )

        self.assertEqual(
            self.fleet_snapshot.get_total_mass_tons(), self.caracal_type.mass / 1000
        )
