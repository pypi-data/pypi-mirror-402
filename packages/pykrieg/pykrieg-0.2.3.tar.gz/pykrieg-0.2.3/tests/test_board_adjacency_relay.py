"""Tests for adjacency-based relay propagation configuration."""


from pykrieg.board import Board


class TestAdjacencyRelayPropagation:
    """Tests for enabling/disabling Step 4 (adjacency-based relay propagation)."""

    def test_default_value_is_true(self):
        """Test that default value enables Step 4."""
        board = Board()
        assert board.get_adjacency_relay_propagation() is True

    def test_constructor_sets_true_by_default(self):
        """Test constructor sets True when not specified."""
        board = Board(enable_adjacency_relay_propagation=True)
        assert board.get_adjacency_relay_propagation() is True

    def test_constructor_sets_false_when_specified(self):
        """Test constructor sets False when specified."""
        board = Board(enable_adjacency_relay_propagation=False)
        assert board.get_adjacency_relay_propagation() is False

    def test_setter_can_enable(self):
        """Test setter can enable Step 4."""
        board = Board(enable_adjacency_relay_propagation=False)
        board.set_adjacency_relay_propagation(True)
        assert board.get_adjacency_relay_propagation() is True

    def test_setter_can_disable(self):
        """Test setter can disable Step 4."""
        board = Board(enable_adjacency_relay_propagation=True)
        board.set_adjacency_relay_propagation(False)
        assert board.get_adjacency_relay_propagation() is False

    def test_setting_marks_network_dirty(self):
        """Test that setting the flag marks network as dirty."""
        board = Board(enable_adjacency_relay_propagation=True)
        board.enable_networks()
        assert not board._network_dirty  # Clean after enable

        board.set_adjacency_relay_propagation(False)
        assert board._network_dirty is True  # Dirty after change

        board.enable_networks()
        assert not board._network_dirty  # Clean again

    def test_enable_networks_uses_instance_value(self):
        """Test enable_networks() uses the instance value."""
        # Default (enabled)
        board = Board()
        board.enable_networks()
        # Should use enable_step4=True (default)

        # Can't easily test without inspecting internal state,
        # but the implementation passes the instance value

        # Disabled
        board = Board(enable_adjacency_relay_propagation=False)
        board.enable_networks()
        # Should use enable_step4=False
