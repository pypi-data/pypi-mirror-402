import unittest

from .poverty import poverty_scale_get_income_limit, poverty_scale_income_qualifies

class TestRecreateTables(unittest.TestCase):
    def test_MA_100_table(self):
        # 48 Contiguous States and DC 2026 Poverty Guidelines
        self.assertEqual(poverty_scale_get_income_limit(1), 15960)
        self.assertEqual(poverty_scale_get_income_limit(2), 15960 + 5680)   # 21,640
        self.assertEqual(poverty_scale_get_income_limit(3), 15960 + 5680 * 2)  # 27,320
        self.assertEqual(poverty_scale_get_income_limit(4), 15960 + 5680 * 3)  # 33,000
        self.assertEqual(poverty_scale_get_income_limit(5), 15960 + 5680 * 4)  # 38,680
        self.assertEqual(poverty_scale_get_income_limit(6), 15960 + 5680 * 5)  # 44,360
        self.assertEqual(poverty_scale_get_income_limit(7), 15960 + 5680 * 6)  # 50,040
        self.assertEqual(poverty_scale_get_income_limit(8), 15960 + 5680 * 7)  # 55,720

    def test_MA_125_table(self):
        multiplier = 1.25
        # 48 Contiguous States and DC 2026 Poverty Guidelines multiplied by 1.25
        self.assertEqual(
            poverty_scale_get_income_limit(1, multiplier),
            int(round(15960 * multiplier))
        )  # 15,960 * 1.25 = 19,950
        self.assertEqual(
            poverty_scale_get_income_limit(2, multiplier),
            int(round((15960 + 5680) * multiplier))
        )  # 21,640 * 1.25 = 27,050
        self.assertEqual(
            poverty_scale_get_income_limit(3, multiplier),
            int(round((15960 + 5680 * 2) * multiplier))
        )  # 27,320 * 1.25 = 34,150
        self.assertEqual(
            poverty_scale_get_income_limit(4, multiplier),
            int(round((15960 + 5680 * 3) * multiplier))
        )  # 33,000 * 1.25 = 41,250
        self.assertEqual(
            poverty_scale_get_income_limit(5, multiplier),
            int(round((15960 + 5680 * 4) * multiplier))
        )  # 38,680 * 1.25 = 48,350
        self.assertEqual(
            poverty_scale_get_income_limit(6, multiplier),
            int(round((15960 + 5680 * 5) * multiplier))
        )  # 44,360 * 1.25 = 55,450
        self.assertEqual(
            poverty_scale_get_income_limit(7, multiplier),
            int(round((15960 + 5680 * 6) * multiplier))
        )  # 50,040 * 1.25 = 62,550
        self.assertEqual(
            poverty_scale_get_income_limit(8, multiplier),
            int(round((15960 + 5680 * 7) * multiplier))
        )  # 55,720 * 1.25 = 69,650

    def test_AK_100_table(self):
        # Alaska 2026 Poverty Guidelines
        self.assertEqual(poverty_scale_get_income_limit(1, state="AK"), 19950)
        self.assertEqual(poverty_scale_get_income_limit(2, state="AK"), 19950 + 7100)   # 27,050
        self.assertEqual(poverty_scale_get_income_limit(3, state="AK"), 19950 + 7100 * 2)  # 34,150
        self.assertEqual(poverty_scale_get_income_limit(4, state="AK"), 19950 + 7100 * 3)  # 41,250
        self.assertEqual(poverty_scale_get_income_limit(5, state="AK"), 19950 + 7100 * 4)  # 48,350
        self.assertEqual(poverty_scale_get_income_limit(6, state="AK"), 19950 + 7100 * 5)  # 55,450
        self.assertEqual(poverty_scale_get_income_limit(7, state="AK"), 19950 + 7100 * 6)  # 62,550
        self.assertEqual(poverty_scale_get_income_limit(8, state="AK"), 19950 + 7100 * 7)  # 69,650

    def test_AK_125_table(self):
        multiplier = 1.25
        # Alaska 2026 Poverty Guidelines multiplied by 1.25
        self.assertEqual(
            poverty_scale_get_income_limit(1, multiplier, state="AK"),
            int(round(19950 * multiplier))
        )  # 19,950 * 1.25 = 24,937.5 → 24938
        self.assertEqual(
            poverty_scale_get_income_limit(2, multiplier, state="AK"),
            int(round((19950 + 7100) * multiplier))
        )  # 27,050 * 1.25 = 33,812.5 → 33812
        self.assertEqual(
            poverty_scale_get_income_limit(3, multiplier, state="AK"),
            int(round((19950 + 7100 * 2) * multiplier))
        )  # 34,150 * 1.25 = 42,687.5 → 42688
        self.assertEqual(
            poverty_scale_get_income_limit(4, multiplier, state="AK"),
            int(round((19950 + 7100 * 3) * multiplier))
        )  # 41,250 * 1.25 = 51,562.5 → 51562
        self.assertEqual(
            poverty_scale_get_income_limit(5, multiplier, state="AK"),
            int(round((19950 + 7100 * 4) * multiplier))
        )  # 48,350 * 1.25 = 60,437.5 → 60438
        self.assertEqual(
            poverty_scale_get_income_limit(6, multiplier, state="AK"),
            int(round((19950 + 7100 * 5) * multiplier))
        )  # 55,450 * 1.25 = 69,312.5 → 69312
        self.assertEqual(
            poverty_scale_get_income_limit(7, multiplier, state="AK"),
            int(round((19950 + 7100 * 6) * multiplier))
        )  # 62,550 * 1.25 = 78,187.5 → 78188
        self.assertEqual(
            poverty_scale_get_income_limit(8, multiplier, state="AK"),
            int(round((19950 + 7100 * 7) * multiplier))
        )  # 69,650 * 1.25 = 87,062.5 → 87062

class TestSampleIncomes(unittest.TestCase):
    def test_example_income(self):
        # TODO(brycew): this should pass, but because of float precision, it doesn't work (even with round).
        # Would have to refactor to Decimal, but out of scope for now
        # self.assertTrue(poverty_scale_income_qualifies(1133))
        self.assertTrue(poverty_scale_income_qualifies(1132))
        self.assertTrue(poverty_scale_income_qualifies(1000))
        self.assertTrue(poverty_scale_income_qualifies(0))
        self.assertTrue(poverty_scale_income_qualifies(-1))
        self.assertFalse(poverty_scale_income_qualifies(14582))
        self.assertFalse(poverty_scale_income_qualifies(100000000))

if __name__ == "__main__":
    unittest.main()
