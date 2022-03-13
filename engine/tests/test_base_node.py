"""Tests the engine.base_node classes Transform, Node and SpriteNode."""

from random import Random
from engine.base_node import Transform, Node, SpriteNode, NodeProperties

def random_transform_values(random):
    return (random.uniform(-999, 999), random.uniform(-999, 999),
            random.randint(-999, 999), random.randint(-999, 999),
            random.uniform(-999, 999), random.uniform(-999, 999))

def test_transform():
    random = Random(1)  # seed ensures consistent random test cases

    test_transforms = [
        Transform(0, 0),
        Transform(11, 2.2, 11, 11, 0.5, 0.5),
        Transform(-11, -2.2, -11, -11, -0.5, -0.5),
    ]
    for i in range(128):
        test_transforms.append(Transform(*random_transform_values(random)))

    print("Test: A transform's 'positive size' has non-negative width and height.")
    for transform in test_transforms:
        positive_size = transform.get_positive_size()
        assert positive_size[0] >= 0 and positive_size[1] >= 0
    print('Test: A transform may be converted to and from a Pygame Rect.'
          + '\n  ... The position and size only stay precise to the nearest integer.')
    for transform in test_transforms:
        rect_transform = Transform.from_rect(
            transform.rect(), transform.anchor_x, transform.anchor_y)
        comparisons = (
            (rect_transform.x, transform.x), (rect_transform.width, transform.width),
            (rect_transform.y, transform.y), (rect_transform.height, transform.height)
        )
        for converted_property, original_property in comparisons:
            assert abs(converted_property - original_property) < 1
        assert rect_transform.anchor == transform.anchor
    print('Test: A transform may be modified by assigning to a property.')
    for transform in test_transforms:
        random_change_in_x = random.uniform(-999, 999)
        t_x, t_y = transform.x, transform.y
        transform.position = (t_x + random_change_in_x, t_y*2)
        assert transform.x == t_x + random_change_in_x and transform.y == t_y*2

def test_node():
    random = Random(1)  # seed ensures consistent random test cases

    class TestScene:
        nodes, is_origin = [], 'Scene'

    a_node = Node(NodeProperties(TestScene))
    b_node = Node(NodeProperties(a_node))
    Node(NodeProperties(b_node))

    print("Test: Initialising a node adds it to its parent's nodes.")
    assert len(TestScene.nodes) == len(a_node.nodes) == len(b_node.nodes) == 1
    print("Test: Removing a node removes it & all child nodes from its parent's nodes.")
    a_node.remove()
    assert len(TestScene.nodes) == len(a_node.nodes) == len(b_node.nodes) == 0

    a_node = Node(NodeProperties(TestScene, *random_transform_values(random)))
    b_node = Node(NodeProperties(a_node, *random_transform_values(random)))

    print('Test: Node rectangle positions depend on and are relative to the parent.')
    for i in range(128):
        random_change_in_x = random.uniform(-999, 999)
        b_node_x_before = b_node.rect.x
        a_node.transform.x += random_change_in_x
        assert abs(b_node.rect.x - (b_node_x_before + random_change_in_x)) < 1

    spr_node = SpriteNode(NodeProperties(a_node))

    print('Test: A sprite node is dirty if it or any parent nodes move or resize.')
    spr_node.dirty = 0
    a_node.transform.x += 1
    assert spr_node.dirty
    spr_node.dirty = 0
    a_node.transform.width += 1
    assert spr_node.dirty

    print('Test: A sprite node is not visible if it or any parent nodes are disabled.')
    a_node.enabled = False
    assert not spr_node.visible
    spr_node.enabled = False
    a_node.enabled = True
    assert not spr_node.visible
    print('Test: A sprite node is visible if it & all parent nodes are enabled.')
    spr_node.enabled = True
    assert spr_node.visible


if __name__ == '__main__':
    test_transform()
    test_node()
