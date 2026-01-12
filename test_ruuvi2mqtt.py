import json
import unittest
import datetime
from unittest.mock import patch, MagicMock, Mock, mock_open
import ruuvi2mqtt

# filepath: /home/rpi/work/ruuvi2mqtt/test_ruuvi2mqtt.py


class TestPublishDiscoveryConfig(unittest.TestCase):

    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1', 'broker2'])
    @patch('ruuvi2mqtt.myhostname', 'testhost')
    @patch('ruuvi2mqtt.logging')
    def test_publish_discovery_config(self, mock_logging, mock_clients):
        mock_clients['broker1'] = MagicMock()
        mock_clients['broker2'] = MagicMock()

        room = 'living_room'
        found_data = ('mac_address', {
            'mac': 'mac_address',
            'temperature': 22.5,
            'humidity': 45,
            'pressure': 1013,
            'battery': 3000,
            'acceleration': 100,
            'acceleration_x': 10,
            'acceleration_y': 20,
            'acceleration_z': 30,
            'rssi': -70,
            'movement_counter': 5
        })

        ruuvi2mqtt.publish_discovery_config(room, found_data)

        # Verify that publish was called with retain=True for discovery messages
        assert mock_clients['broker1'].publish.called
        assert mock_clients['broker2'].publish.called

        # Check that all calls include retain=True
        for call in mock_clients['broker1'].publish.call_args_list:
            args, kwargs = call
            if 'homeassistant/sensor/' in args[0]:  # Discovery topic
                self.assertTrue(kwargs.get('retain', False),
                               f"Discovery message should have retain=True: {args[0]}")

        for call in mock_clients['broker2'].publish.call_args_list:
            args, kwargs = call
            if 'homeassistant/sensor/' in args[0]:  # Discovery topic
                self.assertTrue(kwargs.get('retain', False),
                               f"Discovery message should have retain=True: {args[0]}")


class TestHomeAssistantRestart(unittest.TestCase):

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.logging')
    def test_on_message_homeassistant_restart(self, mock_logging, mock_force_rediscovery):
        """Test that force_rediscovery is called when Home Assistant sends 'online' status."""
        # Create mock MQTT message
        mock_client = MagicMock()
        mock_userdata = None
        mock_properties = None
        mock_msg = MagicMock()
        mock_msg.topic = "homeassistant/status"
        mock_msg.payload.decode.return_value = "online"

        # Call on_message
        ruuvi2mqtt.on_message(mock_client, mock_userdata, mock_msg, mock_properties)

        # Verify force_rediscovery was called
        mock_force_rediscovery.assert_called_once()

        # Verify logging
        mock_logging.info.assert_any_call("Received MQTT message on topic %s: %s",
                                         "homeassistant/status", "online")
        mock_logging.warning.assert_any_call("Home Assistant sent 'online' status - forcing discovery resend")

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.logging')
    def test_on_message_other_status(self, mock_logging, mock_force_rediscovery):
        """Test that force_rediscovery is NOT called for non-'online' messages."""
        # Create mock MQTT message with different payload
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.topic = "homeassistant/status"
        mock_msg.payload.decode.return_value = "offline"

        # Call on_message
        ruuvi2mqtt.on_message(mock_client, None, mock_msg)

        # Verify force_rediscovery was NOT called
        mock_force_rediscovery.assert_not_called()

    @patch('ruuvi2mqtt.logging')
    def test_on_connect_clears_found_ruuvis(self, mock_logging):
        """Test that found_ruuvis is cleared when connecting to broker."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = ['living_room', 'bedroom']

        # Create mock client
        mock_client = MagicMock()
        mock_client.subscribe = MagicMock(return_value=(0, 1))

        # Call on_connect with successful connection (rc=0)
        ruuvi2mqtt.on_connect(mock_client, None, None, 0, None)

        # Verify found_ruuvis was cleared
        self.assertEqual(ruuvi_module.found_ruuvis, [],
                        "found_ruuvis should be cleared on broker connect")

        # Verify subscription
        mock_client.subscribe.assert_called_once_with("homeassistant/status")

        # Verify logging
        mock_logging.info.assert_any_call("MQTT Connection successful")
        mock_logging.info.assert_any_call("Clearing discovery cache to force resend on reconnection")

    @patch('ruuvi2mqtt.logging')
    def test_on_connect_failed_connection(self, mock_logging):
        """Test that on_connect handles failed connections."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = ['living_room']

        # Create mock client
        mock_client = MagicMock()
        mock_client.subscribe = MagicMock()

        # Call on_connect with failed connection (rc != 0)
        ruuvi2mqtt.on_connect(mock_client, None, None, 1, None)

        # Verify error was logged
        mock_logging.error.assert_called_with("Bad MQTT connection, return code: %s", 1)

        # found_ruuvis should NOT be cleared on failed connection
        self.assertEqual(ruuvi_module.found_ruuvis, ['living_room'],
                        "found_ruuvis should not be cleared on failed connection")


class TestForceRediscovery(unittest.TestCase):

    @patch('ruuvi2mqtt.logging')
    def test_force_rediscovery_clears_found_ruuvis(self, mock_logging):
        """Test that force_rediscovery clears the found_ruuvis list."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = ['living_room', 'bedroom', 'kitchen']

        # Call force_rediscovery
        ruuvi2mqtt.force_rediscovery()

        # Verify found_ruuvis was cleared
        self.assertEqual(ruuvi_module.found_ruuvis, [],
                        "force_rediscovery should clear found_ruuvis")

        # Verify logging
        mock_logging.info.assert_called_with("Forcing discovery resend for all %d sensors", 3)

    @patch('ruuvi2mqtt.logging')
    def test_force_rediscovery_empty_list(self, mock_logging):
        """Test that force_rediscovery works with empty list."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = []

        # Call force_rediscovery
        ruuvi2mqtt.force_rediscovery()

        # Verify found_ruuvis is still empty
        self.assertEqual(ruuvi_module.found_ruuvis, [],
                        "force_rediscovery should handle empty list")

        # Verify logging
        mock_logging.info.assert_called_with("Forcing discovery resend for all %d sensors", 0)


class TestHandleDataPeriodicResend(unittest.TestCase):

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1'])
    @patch('ruuvi2mqtt.my_ruuvis', {'AA:BB:CC:DD:EE:FF': 'living_room'})
    @patch('ruuvi2mqtt.logging')
    def test_periodic_discovery_resend_first_time(self, mock_logging, mock_clients,
                                                   mock_publish_discovery, mock_force_rediscovery):
        """Test that periodic discovery resend is triggered on first data."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.last_discovery_resend = None
        ruuvi_module.found_ruuvis = []
        mock_clients['broker1'] = MagicMock()

        # Create test data
        found_data = ('AA:BB:CC:DD:EE:FF', {
            'mac': 'AA:BB:CC:DD:EE:FF',
            'temperature': 22.5,
            'rssi': -70
        })

        # Call handle_data
        ruuvi2mqtt.handle_data(found_data)

        # Verify force_rediscovery was called (first time)
        mock_force_rediscovery.assert_called_once()

        # Verify last_discovery_resend was set
        self.assertIsNotNone(ruuvi_module.last_discovery_resend)

        # Verify logging
        mock_logging.info.assert_any_call("Periodic discovery resend triggered (interval: %d seconds)", 3600)

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1'])
    @patch('ruuvi2mqtt.my_ruuvis', {'AA:BB:CC:DD:EE:FF': 'living_room'})
    @patch('ruuvi2mqtt.logging')
    def test_periodic_discovery_resend_after_interval(self, mock_logging, mock_clients,
                                                       mock_publish_discovery, mock_force_rediscovery):
        """Test that periodic discovery resend is triggered after interval."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state - last resend was more than an hour ago
        past_time = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=3700)
        ruuvi_module.last_discovery_resend = past_time
        ruuvi_module.found_ruuvis = ['living_room']
        mock_clients['broker1'] = MagicMock()

        # Create test data
        found_data = ('AA:BB:CC:DD:EE:FF', {
            'mac': 'AA:BB:CC:DD:EE:FF',
            'temperature': 22.5,
            'rssi': -70
        })

        # Call handle_data
        ruuvi2mqtt.handle_data(found_data)

        # Verify force_rediscovery was called
        mock_force_rediscovery.assert_called_once()

        # Verify last_discovery_resend was updated
        self.assertGreater(ruuvi_module.last_discovery_resend, past_time)

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1'])
    @patch('ruuvi2mqtt.my_ruuvis', {'AA:BB:CC:DD:EE:FF': 'living_room'})
    @patch('ruuvi2mqtt.logging')
    def test_no_periodic_resend_within_interval(self, mock_logging, mock_clients,
                                                 mock_publish_discovery, mock_force_rediscovery):
        """Test that periodic discovery resend is NOT triggered within interval."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state - last resend was just now
        recent_time = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(seconds=100)
        ruuvi_module.last_discovery_resend = recent_time
        ruuvi_module.found_ruuvis = ['living_room']
        mock_clients['broker1'] = MagicMock()

        # Create test data
        found_data = ('AA:BB:CC:DD:EE:FF', {
            'mac': 'AA:BB:CC:DD:EE:FF',
            'temperature': 22.5,
            'rssi': -70
        })

        # Call handle_data
        ruuvi2mqtt.handle_data(found_data)

        # Verify force_rediscovery was NOT called
        mock_force_rediscovery.assert_not_called()

    @patch('ruuvi2mqtt.force_rediscovery')
    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1'])
    @patch('ruuvi2mqtt.my_ruuvis', {'AA:BB:CC:DD:EE:FF': 'living_room'})
    @patch('ruuvi2mqtt.logging')
    def test_handle_data_tracks_last_data_time(self, mock_logging, mock_clients,
                                                mock_publish_discovery, mock_force_rediscovery):
        """Test that handle_data tracks last data time for each sensor."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.last_data_time = {}
        ruuvi_module.last_discovery_resend = datetime.datetime.now(tz=datetime.timezone.utc)
        ruuvi_module.found_ruuvis = ['living_room']
        mock_clients['broker1'] = MagicMock()

        mac = 'AA:BB:CC:DD:EE:FF'
        found_data = (mac, {
            'mac': mac,
            'temperature': 22.5,
            'rssi': -70
        })

        # Call handle_data
        before = datetime.datetime.now(tz=datetime.timezone.utc)
        ruuvi2mqtt.handle_data(found_data)
        after = datetime.datetime.now(tz=datetime.timezone.utc)

        # Verify last_data_time was set for this MAC
        self.assertIn(mac, ruuvi_module.last_data_time)
        self.assertGreaterEqual(ruuvi_module.last_data_time[mac], before)
        self.assertLessEqual(ruuvi_module.last_data_time[mac], after)


class TestHandleDataUnknownSensor(unittest.TestCase):

    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.clients')
    @patch('ruuvi2mqtt.my_brokers', ['broker1'])
    @patch('ruuvi2mqtt.my_ruuvis', {})  # Empty - sensor not configured
    @patch('ruuvi2mqtt.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_handle_unknown_sensor_creates_topic(self, mock_file, mock_logging, mock_clients, mock_publish_discovery):
        """Test that unknown sensors get auto-generated topic names."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = []
        ruuvi_module.last_discovery_resend = datetime.datetime.now(tz=datetime.timezone.utc)
        mock_clients['broker1'] = MagicMock()

        mac = 'AA:BB:CC:DD:EE:FF'
        found_data = (mac, {
            'mac': mac,
            'temperature': 22.5,
            'rssi': -70
        })

        # Call handle_data
        ruuvi2mqtt.handle_data(found_data)

        # Verify auto-generated room name
        expected_room = 'Ruuvi-AABBCCDDEEFF'

        # Verify publish_discovery_config was called with auto-generated room
        mock_publish_discovery.assert_called_once()
        call_args = mock_publish_discovery.call_args[0]
        self.assertEqual(call_args[0], expected_room)

        # Verify warning was logged
        mock_logging.warning.assert_called_with("Not found %s. Using topic home/%s", mac, expected_room)

        # Verify data was written to detected_ruuvis.txt
        mock_file.assert_called_with("detected_ruuvis.txt", "a", encoding="utf-8")


class TestSendSingle(unittest.TestCase):

    @patch('ruuvi2mqtt.logging')
    def test_send_single_publishes_value(self, mock_logging):
        """Test that send_single publishes a single sensor value."""
        # Create mock client
        mock_client = MagicMock()

        # Create test data
        jdata = {
            'room': 'living_room',
            'temperature': 22.5,
            'humidity': 45
        }

        # Call send_single
        ruuvi2mqtt.send_single(jdata, 'temperature', mock_client)

        # Verify publish was called with correct topic and value
        mock_client.publish.assert_called_once_with('living_room/temperature', 22.5)

        # Verify logging
        mock_logging.info.assert_called_with("%s: %s", 'living_room/temperature', 22.5)


class TestOnDisconnect(unittest.TestCase):

    @patch('ruuvi2mqtt.logging')
    def test_on_disconnect_unexpected(self, mock_logging):
        """Test that unexpected disconnection is logged."""
        mock_client = MagicMock()

        # Call on_disconnect with non-zero rc (unexpected disconnect)
        ruuvi2mqtt.on_disconnect(mock_client, None, None, 1, None)

        # Verify error was logged
        mock_logging.error.assert_called_with("Unexpected MQTT disconnection.")

    @patch('ruuvi2mqtt.logging')
    def test_on_disconnect_expected(self, mock_logging):
        """Test that expected disconnection doesn't log error."""
        mock_client = MagicMock()

        # Call on_disconnect with zero rc (expected disconnect)
        ruuvi2mqtt.on_disconnect(mock_client, None, None, 0, None)

        # Verify error was NOT logged
        mock_logging.error.assert_not_called()


class TestConnectBrokers(unittest.TestCase):

    @patch('ruuvi2mqtt.mqtt.Client')
    @patch('ruuvi2mqtt.myhostname', 'testhost')
    @patch('ruuvi2mqtt.logging')
    def test_connect_brokers(self, mock_logging, mock_mqtt_client_class):
        """Test that connect_brokers creates and configures MQTT clients."""
        # Create mock client instance
        mock_client_instance = MagicMock()
        mock_mqtt_client_class.return_value = mock_client_instance

        # Create test broker config
        test_brokers = {
            'broker1': {'host': 'localhost', 'port': 1883},
            'broker2': {'host': '192.168.1.100', 'port': 1883}
        }

        # Reset clients dict
        ruuvi2mqtt.clients = {}

        # Call connect_brokers
        result = ruuvi2mqtt.connect_brokers(test_brokers)

        # Verify Client was created twice
        self.assertEqual(mock_mqtt_client_class.call_count, 2)

        # Verify callbacks were set
        self.assertEqual(mock_client_instance.on_connect, ruuvi2mqtt.on_connect)
        self.assertEqual(mock_client_instance.on_disconnect, ruuvi2mqtt.on_disconnect)
        self.assertEqual(mock_client_instance.on_message, ruuvi2mqtt.on_message)

        # Verify connect_async was called
        self.assertEqual(mock_client_instance.connect_async.call_count, 2)

        # Verify loop_start was called
        self.assertEqual(mock_client_instance.loop_start.call_count, 2)

        # Verify result contains clients
        self.assertIn('broker1', result)
        self.assertIn('broker2', result)


class TestHandleDataPublishesToMQTT(unittest.TestCase):

    @patch('ruuvi2mqtt.publish_discovery_config')
    @patch('ruuvi2mqtt.my_brokers', ['broker1', 'broker2'])
    @patch('ruuvi2mqtt.my_ruuvis', {'AA:BB:CC:DD:EE:FF': 'living_room'})
    @patch('ruuvi2mqtt.myhostname', 'testhost')
    @patch('ruuvi2mqtt.logging')
    def test_handle_data_publishes_to_all_brokers(self, mock_logging, mock_publish_discovery):
        """Test that handle_data publishes sensor data to all configured brokers."""
        ruuvi_module = ruuvi2mqtt

        # Set up initial state
        ruuvi_module.found_ruuvis = ['living_room']
        ruuvi_module.last_discovery_resend = datetime.datetime.now(tz=datetime.timezone.utc)

        # Create mock clients - must be a real dict
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        ruuvi_module.clients = {
            'broker1': mock_client1,
            'broker2': mock_client2
        }

        mac = 'AA:BB:CC:DD:EE:FF'
        found_data = (mac, {
            'mac': mac,
            'temperature': 22.5,
            'humidity': 45,
            'pressure': 1013,
            'rssi': -70
        })

        # Call handle_data
        ruuvi2mqtt.handle_data(found_data)

        # Verify both clients published data
        mock_client1.publish.assert_called_once()
        mock_client2.publish.assert_called_once()

        # Get the published data
        call_args1 = mock_client1.publish.call_args
        topic1 = call_args1[0][0]
        payload1 = call_args1[0][1]

        # Verify topic
        self.assertEqual(topic1, 'home/living_room')

        # Verify payload contains expected data
        data = json.loads(payload1)
        self.assertEqual(data['room'], 'living_room')
        self.assertEqual(data['mac'], mac)
        self.assertEqual(data['temperature'], 22.5)
        self.assertEqual(data['humidity'], 45)
        self.assertEqual(data['client'], 'testhost')
        self.assertIn('ts', data)
        self.assertIn('ts_iso', data)
        self.assertIn('rssi_testhost', data)


if __name__ == '__main__':
    unittest.main()