import time
import pytest
from dialograph import Edge

def test_edge_initialization():
    edge = Edge(source_node_id="n1", target_node_id="n2", relation="supports", strength=0.7)
    
    assert edge.source_node_id == "n1"
    assert edge.target_node_id == "n2"
    assert edge.relation == "supports"
    assert 0.0 <= edge.strength <= 1.0
    assert edge.emotional_charge == 0.0
    assert edge.pending_reinforcement is None
    assert isinstance(edge.created_at, float)
    assert isinstance(edge.last_used, float)

def test_edge_invalid_strength_raises():
    with pytest.raises(ValueError):
        Edge(source_node_id="n1", target_node_id="n2", strength=1.5)

def test_edge_missing_nodes_raises():
    with pytest.raises(ValueError):
        Edge(source_node_id="", target_node_id="n2")


def test_touch_updates_last_used():
    edge = Edge(source_node_id="n1", target_node_id="n2")
    old_time = edge.last_used
    time.sleep(0.01)
    edge.touch()
    assert edge.last_used > old_time


def test_decay_reduces_strength():
    edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.8)
    old_strength = edge.strength
    edge.decay(base_rate=0.1, time_step=10)  # simulate 10s
    assert edge.strength < old_strength
    assert edge.strength >= 0.0

def test_schedule_and_apply_reinforcement_success():
    edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.5)
    edge.schedule_reinforcement(0.3)
    assert edge.pending_reinforcement == 0.3
    edge.apply_reinforcement(success=True)
    assert edge.strength == 0.8
    assert edge.pending_reinforcement is None

def test_apply_reinforcement_failure():
    edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.5)
    edge.schedule_reinforcement(0.4)
    edge.apply_reinforcement(success=False)
    assert edge.strength == pytest.approx(0.5 - 0.2)  # 50% of 0.4

# def test_reinforce_and_weaken():
#     edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.5)
#     edge.reinforce(0.3)
#     assert edge.strength == 0.8
#     edge.weaken(0.2)
#     assert edge.strength == 0.6

def test_register_emotion_and_cool_down():
    edge = Edge(source_node_id="n1", target_node_id="n2")
    edge.register_emotion("happy", intensity=1.0)
    assert edge.emotional_charge > 0
    last_emotion = edge.metadata.get("last_emotion")
    assert last_emotion == "happy"

    old_charge = edge.emotional_charge
    edge.cool_down(rate=old_charge / 2)
    assert edge.emotional_charge < old_charge

def test_importance_score_bounds():
    edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.5)
    score = edge.importance_score()
    assert 0.0 <= score <= 1.0 + 0.2  # emotional boost can add up to +0.2


def test_should_prune():
    edge = Edge(source_node_id="n1", target_node_id="n2", strength=0.05)
    assert edge.should_prune(threshold=0.1)
    edge.strength = 0.2
    assert not edge.should_prune(threshold=0.1)


def test_metadata_update_and_get():
    edge = Edge(source_node_id="n1", target_node_id="n2")
    edge.update_metadata("tag", "test")
    assert edge.get_metadata("tag") == "test"
    assert edge.get_metadata("nonexistent", default=42) == 42

def test_age_and_time_since_use():
    edge = Edge(source_node_id="n1", target_node_id="n2")
    time.sleep(0.01)
    assert edge.age() > 0
    assert edge.time_since_use() > 0
