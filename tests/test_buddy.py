"""
tests/test_buddy.py - Buddy System Tests
"""

import pytest
from h_agent.buddy import (
    Rarity, Species, Eye, Hat, StatName,
    CompanionBones, CompanionSoul, Companion,
    roll, roll_with_seed, generate_companion,
    render_sprite, sprite_frame_count, render_face,
    format_companion_card, format_companion_mini,
    RARITY_WEIGHTS, RARITY_FLOOR, SPECIES_LIST, EYES_LIST, HATS_LIST,
)


class TestCompanionGeneration:
    """Test companion generation logic."""
    
    def test_roll_produces_deterministic_bones(self):
        """Same user_id should always produce same bones."""
        bones1, seed1 = roll("test-user-123")
        bones2, seed2 = roll("test-user-123")
        
        assert bones1.rarity == bones2.rarity
        assert bones1.species == bones2.species
        assert bones1.eye == bones2.eye
        assert bones1.hat == bones2.hat
        assert bones1.shiny == bones2.shiny
        assert bones1.stats == bones2.stats
    
    def test_different_users_get_different_companions(self):
        """Different user_ids should (usually) produce different companions."""
        bones1, _ = roll("user-alice")
        bones2, _ = roll("user-bob")
        
        # At least one attribute should differ
        different = (
            bones1.rarity != bones2.rarity or
            bones1.species != bones2.species or
            bones1.eye != bones2.eye
        )
        assert different, "Different users should get different companions"
    
    def test_roll_with_seed_is_deterministic(self):
        """Using same seed string should produce same results."""
        bones1, seed1 = roll_with_seed("fixed-seed")
        bones2, seed2 = roll_with_seed("fixed-seed")
        
        assert bones1.rarity == bones2.rarity
        assert bones1.species == bones2.species
    
    def test_generate_companion_returns_full_companion(self):
        """generate_companion should return Companion with bones + soul."""
        companion = generate_companion("test-user")
        
        assert isinstance(companion, Companion)
        assert isinstance(companion.rarity, Rarity)
        assert isinstance(companion.species, Species)
        assert isinstance(companion.eye, Eye)
        assert isinstance(companion.hat, Hat)
        assert isinstance(companion.stats, dict)
        assert companion.name is not None
        assert companion.personality is not None
        assert companion.hatched_at > 0


class TestRarity:
    """Test rarity distribution."""
    
    def test_all_rarities_exist(self):
        """All expected rarities should exist."""
        assert Rarity.COMMON in RARITY_WEIGHTS
        assert Rarity.UNCOMMON in RARITY_WEIGHTS
        assert Rarity.RARE in RARITY_WEIGHTS
        assert Rarity.EPIC in RARITY_WEIGHTS
        assert Rarity.LEGENDARY in RARITY_WEIGHTS
    
    def test_rarity_weights_sum_to_100(self):
        """Rarity weights should sum to 100 for percentage calculation."""
        total = sum(RARITY_WEIGHTS.values())
        assert total == 100
    
    def test_common_has_highest_weight(self):
        """Common should have highest weight."""
        assert RARITY_WEIGHTS[Rarity.COMMON] > RARITY_WEIGHTS[Rarity.LEGENDARY]
    
    def test_rarity_floor_increases_with_rarity(self):
        """Higher rarities should have higher stat floors."""
        assert RARITY_FLOOR[Rarity.COMMON] < RARITY_FLOOR[Rarity.RARE]
        assert RARITY_FLOOR[Rarity.RARE] < RARITY_FLOOR[Rarity.EPIC]
        assert RARITY_FLOOR[Rarity.EPIC] < RARITY_FLOOR[Rarity.LEGENDARY]


class TestSpecies:
    """Test species enumeration."""
    
    def test_all_species_exist(self):
        """All expected species should exist."""
        expected = [
            Species.DUCK, Species.GOOSE, Species.BLOB, Species.CAT,
            Species.DRAGON, Species.OCTOPUS, Species.OWL, Species.PENGUIN,
            Species.TURTLE, Species.SNAIL, Species.GHOST, Species.AXOLOTL,
            Species.CAPYBARA, Species.CACTUS, Species.ROBOT, Species.RABBIT,
            Species.MUSHROOM, Species.CHONK,
        ]
        for s in expected:
            assert s in SPECIES_LIST
    
    def test_sprite_frame_count_is_positive(self):
        """Each species should have at least one frame."""
        for species in SPECIES_LIST:
            count = sprite_frame_count(species)
            assert count > 0, f"{species} should have at least one frame"


class TestStats:
    """Test stat generation."""
    
    def test_stats_are_within_range(self):
        """Stats should be between 1 and 100."""
        bones, _ = roll("test-user")
        
        for name, value in bones.stats.items():
            assert 1 <= value <= 100, f"{name} should be 1-100, got {value}"
    
    def test_all_stats_present(self):
        """All stat names should be present."""
        bones, _ = roll("test-user")
        
        expected_stats = {s.value for s in StatName}
        actual_stats = set(bones.stats.keys())
        
        assert expected_stats == actual_stats, f"Expected {expected_stats}, got {actual_stats}"
    
    def test_shiny_is_rare(self):
        """Shiny should be very rare (1% chance)."""
        shiny_count = 0
        trials = 1000
        
        for i in range(trials):
            bones, _ = roll(f"shiny-test-{i}")
            if bones.shiny:
                shiny_count += 1
        
        # Should be roughly 1% (allow some variance)
        ratio = shiny_count / trials
        assert 0 < ratio < 0.05, f"Shiny rate should be ~1%, got {ratio:.2%}"


class TestSprites:
    """Test sprite rendering."""
    
    def test_render_sprite_returns_lines(self):
        """render_sprite should return a list of strings."""
        bones, _ = roll("test-user")
        lines = render_sprite(bones)
        
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert all(isinstance(line, str) for line in lines)
    
    def test_render_sprite_substitutes_eyes(self):
        """Eye {E} placeholder should be replaced."""
        bones, _ = roll("test-user")
        lines = render_sprite(bones)
        
        eye_str = bones.eye.value
        for line in lines:
            assert "{E}" not in line, f"Eye placeholder not replaced in: {line}"
            # The eye character should appear in appropriate lines
            if eye_str in ["·", "✦", "×", "◉", "@", "°"]:
                # Just verify no leftover placeholder
                pass
    
    def test_render_face_returns_string(self):
        """render_face should return a string."""
        bones, _ = roll("test-user")
        face = render_face(bones)
        
        assert isinstance(face, str)
        assert len(face) > 0


class TestDisplay:
    """Test display formatting."""
    
    def test_format_companion_card(self):
        """format_companion_card should return formatted string."""
        companion = generate_companion("test-user")
        card = format_companion_card(companion)
        
        assert isinstance(card, str)
        assert len(card) > 0
        assert companion.name in card
        # Card shows rarity in uppercase
        assert companion.rarity.value.upper() in card
    
    def test_format_companion_mini(self):
        """format_companion_mini should return compact formatted string."""
        companion = generate_companion("test-user")
        mini = format_companion_mini(companion)
        
        assert isinstance(mini, str)
        assert len(mini) > 0
        assert companion.name in mini


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
