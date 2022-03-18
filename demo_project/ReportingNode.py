import engine.base_node

class ReportingNode(engine.base_node.Node):
    def __init__(self, node_props):
        super().__init__(node_props)
        print(f'Initialised {self}.')
