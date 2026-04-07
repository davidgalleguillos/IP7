import pytest
from ipv7.ipv7_header import IPv7Header, GeoLocation, QoSLevel
from ipv7.ipv7_core import IPv7Router, RoutingEntry
from ipv7.utils import IPv7Address, PacketValidator, NetworkDiagnostics

@pytest.fixture
def sample_header():
    return IPv7Header(
        source=b'\x00' * 32,
        destination=b'\x01' * 32,
        traffic_priority=1,
        payload_length=100,
        next_header=0,
        hop_limit=64,
        qos_level=QoSLevel.BEST_EFFORT,
        geo_location=GeoLocation(40.7128, -74.0060),
        encryption_enabled=False,
        encryption_algorithm=None
    )

@pytest.fixture
def router():
    return IPv7Router()

class TestIPv7Header:
    def test_header_pack_unpack(self, sample_header):
        packed = sample_header.pack()
        unpacked = IPv7Header.unpack(packed)
        assert unpacked.version == 7
        assert unpacked.source == sample_header.source
        assert unpacked.destination == sample_header.destination
        assert unpacked.traffic_priority == sample_header.traffic_priority
        assert unpacked.qos_level == sample_header.qos_level
        
    def test_geo_location(self, sample_header):
        assert sample_header.geo_location.latitude == 40.7128
        assert sample_header.geo_location.longitude == -74.0060
        
    def test_invalid_version(self):
        with pytest.raises(ValueError):
            IPv7Header.unpack(b'\x06' + b'\x00' * 100)  # Version 6

class TestIPv7Router:
    @pytest.mark.asyncio
    async def test_send_packet(self, router, sample_header):
        # Añadir ruta necesaria para el test
        router.add_route(sample_header.destination, RoutingEntry(
            next_hop=b'\x02' * 32,
            metric=1,
            interface="eth0",
            qos_capabilities=[QoSLevel.BEST_EFFORT]
        ))
        result = await router.send(sample_header, b"Test payload")
        assert result == True
        
    def test_fragmentation(self, router, sample_header):
        large_payload = b"X" * 10000
        fragments = router._fragment_if_needed(sample_header, large_payload)
        assert len(fragments) > 1
        total_size = sum(len(p) for _, p in fragments)
        assert total_size == len(large_payload)
        
    def test_routing_table(self, router):
        entry = RoutingEntry(
            next_hop=b'\x02' * 32,
            metric=1,
            interface="eth0",
            qos_capabilities=[QoSLevel.BEST_EFFORT]
        )
        router.add_route(b'\x01' * 32, entry)
        assert b'\x01' * 32 in router.routing_table
        router.remove_route(b'\x01' * 32)
        assert b'\x01' * 32 not in router.routing_table

class TestIPv7Address:
    def test_valid_address(self):
        addr = "q256:" + "0" * 64
        assert IPv7Address.is_valid(addr)
        
    def test_invalid_address(self):
        with pytest.raises(ValueError):
            IPv7Address("invalid")
            
    def test_ipv6_conversion(self):
        v6_addr = "2001:db8::1"
        v7_addr = IPv7Address.from_ipv6(v6_addr)
        assert IPv7Address.is_valid(str(v7_addr))

class TestPacketValidator:
    def test_header_validation(self, sample_header):
        valid, error = PacketValidator.validate_header(sample_header)
        assert valid
        assert error is None
        
    def test_geo_validation(self):
        valid, error = PacketValidator.validate_geo_location(
            GeoLocation(90.1, 0)
        )
        assert not valid
        assert "latitude" in error.lower()

@pytest.mark.asyncio
class TestNetworkDiagnostics:
    async def test_traceroute(self):
        dest = IPv7Address("q256:" + "0" * 64)
        results = await NetworkDiagnostics.traceroute(dest, max_hops=5)
        assert len(results) <= 5
        assert all('hop' in r for r in results)
        
    async def test_mtu_discovery(self):
        dest = IPv7Address("q256:" + "0" * 64)
        mtu = await NetworkDiagnostics.mtu_discovery(dest)
        assert 1280 <= mtu <= 9000
        
    async def test_latency(self):
        dest = IPv7Address("q256:" + "0" * 64)
        results = await NetworkDiagnostics.measure_latency(dest, samples=2)
        assert QoSLevel.BEST_EFFORT.name in results
        assert 'min' in results[QoSLevel.BEST_EFFORT.name]