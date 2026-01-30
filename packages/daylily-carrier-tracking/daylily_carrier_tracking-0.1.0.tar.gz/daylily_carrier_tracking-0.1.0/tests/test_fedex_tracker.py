import unittest
from unittest.mock import patch


class _Resp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class TestFedexTracker(unittest.TestCase):
    def _cfg(self):
        return {
            "api_url": "https://apis.fedex.com/oauth/token",
            "client_id": "id",
            "client_secret": "secret",
            "track_url": "https://apis.fedex.com/track/v1/trackingnumbers",
            "ship_track_url": "https://apis.fedex.com/ship/v1/trackingnumbers",
        }

    def test_normalize_valid_minimal(self):
        from daylily_carrier_tracking.fedex_tracker import normalize_fedex_track_ops_meta

        raw = {
            "output": {
                "completeTrackResults": [
                    {
                        "trackResults": [
                            {
                                "latestStatusDetail": {"statusByLocale": "Delivered"},
                                "dateAndTimes": [
                                    {"type": "ACTUAL_DELIVERY", "dateTime": "2023-06-27T11:34:00+00:00"},
                                    {"type": "SHIP", "dateTime": "2023-06-26T00:00:00-06:00"},
                                ],
                                "originLocation": {
                                    "locationContactAndAddress": {"address": {"stateOrProvinceCode": "CA", "city": "VALENCIA"}}
                                },
                                "lastUpdatedDestinationAddress": {"stateOrProvinceCode": "CA", "city": "OAKLAND"},
                                "serviceDetail": {"shortDescription": "P-2"},
                            }
                        ]
                    }
                ]
            }
        }

        ops = normalize_fedex_track_ops_meta(raw)
        self.assertEqual(ops["Delivery_Status"], "Delivered")
        self.assertEqual(ops["Origin_state"], "CA")
        self.assertEqual(ops["Destination_state"], "CA")
        self.assertEqual(ops["Delivery_weekday"], "Tuesday")
        self.assertTrue(isinstance(ops["Transit_Time_sec"], (int, float)))
        self.assertGreater(ops["Transit_Time_sec"], 0)
        self.assertEqual(ops["Destination_state_alt"], "P-2")

    def test_normalize_notfound_matches_readme_defaults(self):
        from daylily_carrier_tracking.fedex_tracker import normalize_fedex_track_ops_meta

        raw = {
            "output": {
                "completeTrackResults": [
                    {"trackResults": [{"error": {"code": "TRACKING.TRACKINGNUMBER.NOTFOUND"}}]}
                ]
            }
        }
        ops = normalize_fedex_track_ops_meta(raw)
        self.assertEqual(ops["Delivery_Status"], "na")
        self.assertEqual(ops["Origin_state"], "na")
        self.assertEqual(ops["Destination_state"], "na")
        self.assertEqual(ops["Transit_Time_sec"], -1)

    @patch("daylily_carrier_tracking.fedex_tracker.requests.post")
    def test_auto_fallback_to_ship_on_notfound(self, post):
        from daylily_carrier_tracking.fedex_tracker import FedexTracker

        oauth_ok = _Resp(200, {"access_token": "tok", "expires_in": 3600})
        track_notfound = _Resp(
            200,
            {
                "output": {
                    "completeTrackResults": [
                        {"trackResults": [{"error": {"code": "TRACKING.TRACKINGNUMBER.NOTFOUND"}}]}
                    ]
                }
            },
        )
        ship_ok = _Resp(
            200,
            {
                "output": {
                    "completeTrackResults": [
                        {
                            "trackResults": [
                                {
                                    "latestStatusDetail": {"statusByLocale": "Delivered"},
                                    "dateAndTimes": [{"type": "ACTUAL_DELIVERY", "dateTime": "2023-06-27T11:34:00+00:00"}],
                                    "originLocation": {
                                        "locationContactAndAddress": {"address": {"stateOrProvinceCode": "CA", "city": "VALENCIA"}}
                                    },
                                    "lastUpdatedDestinationAddress": {"stateOrProvinceCode": "CA", "city": "OAKLAND"},
                                }
                            ]
                        }
                    ]
                }
            },
        )

        # Order: oauth, track, ship
        post.side_effect = [oauth_ok, track_notfound, ship_ok]

        tracker = FedexTracker(config=self._cfg())
        out = tracker.track("X", api_preference="auto", include_raw=False)
        self.assertEqual(out["source"]["api"], "ship_v1")
        self.assertEqual(out["ops_meta"]["Delivery_Status"], "Delivered")


if __name__ == "__main__":
    unittest.main()
