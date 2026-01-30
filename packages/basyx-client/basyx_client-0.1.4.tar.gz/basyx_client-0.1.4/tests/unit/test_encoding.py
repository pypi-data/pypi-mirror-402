"""Unit tests for encoding utilities."""

from basyx_client.encoding import (
    decode_id_short_path,
    decode_identifier,
    encode_id_short_path,
    encode_identifier,
)


class TestEncodeIdentifier:
    """Tests for encode_identifier function."""

    def test_encode_simple_url(self) -> None:
        """Test encoding a simple URL identifier."""
        identifier = "https://acme.org/ids/aas/55"
        encoded = encode_identifier(identifier)

        # Should not contain padding
        assert "=" not in encoded
        # Should be decodable
        assert decode_identifier(encoded) == identifier

    def test_encode_urn(self) -> None:
        """Test encoding a URN identifier."""
        identifier = "urn:example:aas:machine:12345"
        encoded = encode_identifier(identifier)

        assert "=" not in encoded
        assert decode_identifier(encoded) == identifier

    def test_encode_special_characters(self) -> None:
        """Test encoding identifiers with special characters."""
        identifier = "https://example.com/aas?id=123&version=1.0"
        encoded = encode_identifier(identifier)

        assert "=" not in encoded
        assert decode_identifier(encoded) == identifier

    def test_encode_unicode(self) -> None:
        """Test encoding identifiers with unicode characters."""
        identifier = "https://example.com/aas/机器-123"
        encoded = encode_identifier(identifier)

        assert "=" not in encoded
        assert decode_identifier(encoded) == identifier

    def test_round_trip_various_lengths(self) -> None:
        """Test that encoding/decoding works for various input lengths."""
        # Different lengths produce different padding requirements
        test_cases = [
            "a",  # 1 char
            "ab",  # 2 chars
            "abc",  # 3 chars
            "abcd",  # 4 chars
            "https://acme.org/ids/aas/machine-with-long-identifier-12345",
        ]

        for identifier in test_cases:
            encoded = encode_identifier(identifier)
            assert "=" not in encoded, f"Padding found for {identifier!r}"
            decoded = decode_identifier(encoded)
            assert decoded == identifier, f"Round-trip failed for {identifier!r}"


class TestDecodeIdentifier:
    """Tests for decode_identifier function."""

    def test_decode_with_missing_padding(self) -> None:
        """Test decoding restores missing padding."""
        # This is base64url of "test" without padding
        encoded = "dGVzdA"
        decoded = decode_identifier(encoded)
        assert decoded == "test"

    def test_decode_various_padding_amounts(self) -> None:
        """Test decoding with different padding requirements."""
        # 0 padding needed (len % 4 == 0)
        # 1 padding needed (len % 4 == 3)
        # 2 padding needed (len % 4 == 2)
        # 3 padding needed (len % 4 == 1) - but this is invalid base64

        test_cases = [
            ("YQ", "a"),  # needs 2 padding
            ("YWI", "ab"),  # needs 1 padding
            ("YWJj", "abc"),  # needs 0 padding
        ]

        for encoded, expected in test_cases:
            assert decode_identifier(encoded) == expected


class TestEncodeIdShortPath:
    """Tests for encode_id_short_path function."""

    def test_encode_simple_path(self) -> None:
        """Test encoding a simple path (no special chars)."""
        path = "Temperature"
        encoded = encode_id_short_path(path)

        # Simple paths should remain unchanged
        assert encoded == "Temperature"

    def test_encode_dotted_path(self) -> None:
        """Test that dots are preserved."""
        path = "Sensors.Data.Temperature"
        encoded = encode_id_short_path(path)

        # Dots should be preserved
        assert encoded == "Sensors.Data.Temperature"

    def test_encode_array_indices(self) -> None:
        """Test encoding paths with array indices."""
        path = "Sensors.Measurements[0].Temperature"
        encoded = encode_id_short_path(path)

        # Brackets should be encoded
        assert "[" not in encoded
        assert "]" not in encoded
        assert "%5B" in encoded  # [
        assert "%5D" in encoded  # ]
        assert encoded == "Sensors.Measurements%5B0%5D.Temperature"

    def test_encode_multiple_array_indices(self) -> None:
        """Test encoding paths with multiple array indices."""
        path = "Data[0].Items[1].Value"
        encoded = encode_id_short_path(path)

        assert encoded == "Data%5B0%5D.Items%5B1%5D.Value"
        assert decode_id_short_path(encoded) == path

    def test_preserve_safe_characters(self) -> None:
        """Test that safe characters are preserved."""
        path = "Property-Name_123.Sub~Value"
        encoded = encode_id_short_path(path)

        # Hyphens, underscores, dots, tildes should be preserved
        assert "-" in encoded
        assert "_" in encoded
        assert "." in encoded
        assert "~" in encoded


class TestDecodeIdShortPath:
    """Tests for decode_id_short_path function."""

    def test_decode_encoded_path(self) -> None:
        """Test decoding an encoded path."""
        encoded = "Sensors.Measurements%5B0%5D.Temperature"
        decoded = decode_id_short_path(encoded)

        assert decoded == "Sensors.Measurements[0].Temperature"

    def test_round_trip(self) -> None:
        """Test encoding and decoding is reversible."""
        original = "ComplexPath[0].Sub[1].Element"
        encoded = encode_id_short_path(original)
        decoded = decode_id_short_path(encoded)

        assert decoded == original


class TestRealWorldScenarios:
    """Test real-world encoding scenarios from AAS API usage."""

    def test_typical_aas_id(self, sample_aas_id: str) -> None:
        """Test encoding typical AAS identifier."""
        encoded = encode_identifier(sample_aas_id)

        # Should be URL-safe
        assert "/" not in encoded
        assert ":" not in encoded
        assert "=" not in encoded

        # Should round-trip
        assert decode_identifier(encoded) == sample_aas_id

    def test_typical_submodel_id(self, sample_submodel_id: str) -> None:
        """Test encoding typical Submodel identifier."""
        encoded = encode_identifier(sample_submodel_id)

        assert decode_identifier(encoded) == sample_submodel_id

    def test_typical_id_short_path(self, sample_id_short_path: str) -> None:
        """Test encoding typical idShortPath."""
        encoded = encode_id_short_path(sample_id_short_path)

        assert decode_id_short_path(encoded) == sample_id_short_path
        assert "%5B" in encoded  # [ encoded
        assert "%5D" in encoded  # ] encoded
